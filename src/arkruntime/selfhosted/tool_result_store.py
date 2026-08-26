# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

from .types import ContentBlock, Event, new_user_custom_tool_result_event, new_user_tool_result_event, utc_now_iso

STATE_STARTED = "started"
STATE_RESULT = "result"
STATE_SENT = "sent"


@dataclass
class ToolCallStoreDecision:
    sent: bool = False
    result: Event = None  # type: ignore[assignment]


class FileToolResultStore:
    """File-backed ledger that avoids re-running side-effectful tool calls."""

    def __init__(self, workdir: str) -> None:
        if not workdir:
            raise ValueError("workdir must not be empty")
        self.dir = Path(workdir) / ".ma_self_host_worker" / "tool_ledger"
        self.dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def recover(self) -> Tuple[Dict[str, Event], Dict[str, bool]]:
        pending: Dict[str, Event] = {}
        processed: Dict[str, bool] = {}
        for path in self.dir.glob(".tool-result-*.tmp"):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        for path in self.dir.glob("*.json"):
            record = self._read_path(path)
            call_id = str(record.get("call_id") or "")
            state = str(record.get("state") or "")
            if not call_id:
                raise ValueError(f"tool result record {path} missing call_id")
            if state == STATE_SENT:
                processed[call_id] = True
            elif state == STATE_RESULT:
                pending[call_id] = Event.from_mapping(record.get("result") or {})
            elif state == STATE_STARTED:
                event = Event.from_mapping(record.get("event") or {})
                result = _unknown_tool_execution_result(call_id, event)
                record["result"] = result.to_dict()
                record["state"] = STATE_RESULT
                self._write_record(record)
                pending[call_id] = result
            else:
                raise ValueError(f"unknown tool result state {state!r} for call {call_id}")
        return pending, processed

    def begin(self, call_id: str, event: Event) -> ToolCallStoreDecision:
        if not call_id:
            raise ValueError("call id must not be empty")
        try:
            record = self._read(call_id)
        except FileNotFoundError:
            self._write_record({"call_id": call_id, "state": STATE_STARTED, "event": event.to_dict()})
            return ToolCallStoreDecision()
        state = str(record.get("state") or "")
        if state == STATE_SENT:
            return ToolCallStoreDecision(sent=True)
        if state == STATE_RESULT:
            return ToolCallStoreDecision(result=Event.from_mapping(record.get("result") or {}))
        if state == STATE_STARTED:
            result = _unknown_tool_execution_result(call_id, Event.from_mapping(record.get("event") or {}))
            record["result"] = result.to_dict()
            record["state"] = STATE_RESULT
            self._write_record(record)
            return ToolCallStoreDecision(result=result)
        raise ValueError(f"unknown tool result state {state!r} for call {call_id}")

    def save_result(self, call_id: str, result: Event) -> None:
        record = self._read(call_id)
        record["state"] = STATE_RESULT
        record["result"] = result.to_dict()
        self._write_record(record)

    def mark_sent(self, call_id: str) -> None:
        record = self._read(call_id)
        record["state"] = STATE_SENT
        self._write_record(record)

    def _read(self, call_id: str) -> dict:
        return self._read_path(self._path(call_id))

    def _read_path(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_record(self, record: dict) -> None:
        call_id = str(record.get("call_id") or "")
        if not call_id:
            raise ValueError("call id must not be empty")
        record["updated_at"] = utc_now_iso()
        target = self._path(call_id)
        fd, tmp = tempfile.mkstemp(prefix=".tool-result-", suffix=".tmp", dir=self.dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                fd = -1
                json.dump(record, output, ensure_ascii=False, indent=2)
                output.flush()
                os.fsync(output.fileno())
            os.replace(tmp, target)
            _sync_directory(self.dir)
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                os.remove(tmp)
            except FileNotFoundError:
                pass

    def _path(self, call_id: str) -> Path:
        digest = hashlib.sha256(call_id.encode("utf-8")).hexdigest()
        return self.dir / f"{digest}.json"


def _unknown_tool_execution_result(call_id: str, event: Event) -> Event:
    content = [
        ContentBlock(
            type="text",
            text=(
                "tool execution state is unknown after worker restart; refusing to re-execute this tool_use "
                "to avoid duplicate side effects"
            ),
        )
    ]
    if event.type == "agent.custom_tool_use":
        return new_user_custom_tool_result_event(call_id, content, True, event.session_thread_id)
    return new_user_tool_result_event(call_id, content, True, event.session_thread_id)


def _sync_directory(path: Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        # Some non-POSIX filesystems do not support syncing directories.
        pass
    finally:
        os.close(fd)
