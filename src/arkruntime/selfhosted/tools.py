# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import glob as globlib
import json
import os
import re
import signal
import stat
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from .types import DEFAULT_TOOL_TIMEOUT_SECONDS, ContentBlock

MAX_OUTPUT_BYTES = 100000
MAX_SEARCH_MATCHES = 1000
_SENSITIVE_ENV_PREFIXES = (
    "AIME_",
    "ARK_",
    "MA_",
    "X_CODE_",
    "ANTHROPIC_",
    "OPENAI_",
    "AWS_",
    "AZURE_",
    "GOOGLE_",
)
_SENSITIVE_ENV_NAMES = {
    "VOLC_ACCESSKEY",
    "VOLC_SECRETKEY",
    "BYTEPLUS_ACCESSKEY",
    "BYTEPLUS_SECRETKEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "PRIVATE_KEY",
    "API_KEY",
    "ACCESS_KEY",
    "SECRET_KEY",
    "JWT",
    "PAT",
}
_SENSITIVE_ENV_SUFFIXES = (
    "_TOKEN",
    "_SECRET",
    "_PASSWORD",
    "_PASSWD",
    "_PRIVATE_KEY",
    "_API_KEY",
    "_ACCESS_KEY",
    "_SECRET_KEY",
    "_JWT",
    "_PAT",
)


@dataclass
class ToolResult:
    content: Iterable[ContentBlock]
    is_error: bool = False


class Tool:
    """Tool contract; the runner enforces timeouts and tools should release promptly on cancellation."""

    name: str

    def execute(self, tool_input: Any, context: "ToolContext") -> ToolResult:
        raise NotImplementedError


@dataclass
class ToolContext:
    workdir: str
    env: Optional[Dict[str, str]] = None
    unrestricted_paths: bool = False
    tool_timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS
    cancel_event: Any = None


class FunctionTool(Tool):
    def __init__(self, name: str, fn: Callable[[Any, ToolContext], ToolResult]) -> None:
        self.name = name
        self._fn = fn

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        return self._fn(tool_input, context)


class ToolSet:
    def __init__(self, tools: Optional[Iterable[Tool]] = None) -> None:
        self._tools: Dict[str, Tool] = {}
        for tool in tools or []:
            self.add(tool)

    def add(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError("tool name must not be empty")
        self._tools[tool.name] = tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def execute(self, name: str, tool_input: Any, context: ToolContext) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return error_result(f"tool {name!r} is not registered")
        try:
            return tool.execute(tool_input, context)
        except Exception as exc:  # noqa: BLE001 - tool errors must be reported, not raised.
            return error_result(str(exc))


class BashTool(Tool):
    name = "bash"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        command = str(args.get("command") or args.get("cmd") or "")
        if not command:
            return error_result("bash command is required")
        env = _scrubbed_env(context.env)
        proc = subprocess.Popen(  # noqa: S602 - this is the explicit bash tool contract.
            command,
            shell=True,
            cwd=context.workdir,
            env=env,
            text=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        output = _BoundedOutput(MAX_OUTPUT_BYTES)
        reader = threading.Thread(target=_drain_output, args=(proc.stdout, output), daemon=True)
        reader.start()
        deadline = time.monotonic() + max(context.tool_timeout_seconds, 0)
        failure = ""
        while proc.poll() is None:
            if _is_cancelled(context):
                failure = "tool execution canceled"
                _kill_process(proc)
                break
            if context.tool_timeout_seconds > 0 and time.monotonic() >= deadline:
                failure = f"tool execution timed out after {context.tool_timeout_seconds:g}s"
                _kill_process(proc)
                break
            time.sleep(0.05)
        proc.wait()
        reader.join(timeout=1)
        text = output.text()
        if failure:
            return error_result(f"{failure}\n{text}".rstrip())
        if proc.returncode != 0:
            text = f"exit code {proc.returncode}\n{text}" if text else f"exit code {proc.returncode}"
        return text_result(text, is_error=proc.returncode != 0)


class ReadFileTool(Tool):
    name = "read"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        path = _safe_path(context, str(args.get("path") or args.get("file") or ""))
        limit = min(max(int(args.get("limit") or 20000), 0), MAX_OUTPUT_BYTES)
        offset = int(args.get("offset") or 0)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            if offset > 0:
                f.seek(offset)
            return text_result(f.read(limit))


class WriteFileTool(Tool):
    name = "write"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        raw_path = str(args.get("path") or args.get("file") or "")
        path = _safe_path(context, raw_path)
        content = str(args.get("content") or "")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        verified = _safe_path(context, raw_path)
        if verified != path:
            raise ValueError("path resolution changed while writing")
        _write_file_atomically(path, content.encode("utf-8"), 0o600)
        return text_result(f"wrote {len(content)} bytes")


class EditFileTool(Tool):
    name = "edit"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        raw_path = str(args.get("path") or args.get("file") or "")
        path = _safe_path(context, raw_path)
        old = str(args.get("old_string") or args.get("old") or "")
        new = str(args.get("new_string") or args.get("new") or "")
        if not old:
            return error_result("old_string is required")
        data = Path(path).read_text(encoding="utf-8")
        if old not in data:
            return error_result("old_string was not found")
        mode = stat.S_IMODE(os.stat(path).st_mode)
        verified = _safe_path(context, raw_path)
        if verified != path:
            raise ValueError("path resolution changed while editing")
        _write_file_atomically(path, data.replace(old, new, 1).encode("utf-8"), mode)
        return text_result("edited")


class GlobTool(Tool):
    name = "glob"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        pattern = str(args.get("pattern") or "")
        if not pattern:
            return error_result("pattern is required")
        root = Path(context.workdir).resolve()
        matches = []
        for match in globlib.glob(str(root / pattern), recursive=True):
            if _is_cancelled(context):
                return error_result("tool execution canceled")
            try:
                resolved = Path(match).resolve()
                if context.unrestricted_paths or resolved == root or root in resolved.parents:
                    matches.append(str(resolved.relative_to(root)) if root in resolved.parents else str(resolved))
                    if len(matches) >= MAX_SEARCH_MATCHES:
                        break
            except (OSError, ValueError):
                continue
        return text_result(_truncate("\n".join(sorted(matches))))


class GrepTool(Tool):
    name = "grep"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        pattern = str(args.get("pattern") or args.get("query") or "")
        target = str(args.get("path") or ".")
        if not pattern:
            return error_result("pattern is required")
        root = _safe_path(context, target)
        rx = re.compile(pattern)
        lines = []
        paths: Iterable[str] = [root]
        if os.path.isdir(root):
            paths = (os.path.join(base, name) for base, _, names in os.walk(root) for name in names)
        for path in paths:
            if _is_cancelled(context):
                return error_result("tool execution canceled")
            try:
                verified = _safe_path(context, path)
                with open(verified, "r", encoding="utf-8", errors="replace") as f:
                    for number, line in enumerate(f, 1):
                        if _is_cancelled(context):
                            return error_result("tool execution canceled")
                        if rx.search(line):
                            rel = os.path.relpath(path, context.workdir)
                            lines.append(f"{rel}:{number}:{line.rstrip()}")
                            if len(lines) >= 200 or sum(len(value) + 1 for value in lines) >= MAX_OUTPUT_BYTES:
                                return text_result(_truncate("\n".join(lines)))
            except (OSError, ValueError):
                continue
        return text_result("\n".join(lines))


def default_toolset() -> ToolSet:
    return ToolSet([BashTool(), ReadFileTool(), WriteFileTool(), EditFileTool(), GlobTool(), GrepTool()])


def text_result(text: str, *, is_error: bool = False) -> ToolResult:
    return ToolResult([ContentBlock(type="text", text=text)], is_error=is_error)


def error_result(text: str) -> ToolResult:
    return text_result(text, is_error=True)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            return {"command": value}
        if isinstance(parsed, Mapping):
            return parsed
    return {}


def _safe_path(context: ToolContext, path: str) -> str:
    if not path:
        raise ValueError("path is required")
    root = Path(context.workdir).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    resolved = target.resolve()
    if context.unrestricted_paths:
        return str(resolved)
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes workdir: {path}")
    return str(resolved)


def _truncate(text: str, limit: int = 100000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... truncated ..."


def _is_cancelled(context: ToolContext) -> bool:
    return bool(context.cancel_event and context.cancel_event.is_set())


def _is_sensitive_env_key(key: str) -> bool:
    upper = key.strip().upper()
    return (
        upper.startswith(_SENSITIVE_ENV_PREFIXES)
        or upper in _SENSITIVE_ENV_NAMES
        or upper.endswith(_SENSITIVE_ENV_SUFFIXES)
    )


def _scrubbed_env(extra: Optional[Mapping[str, str]]) -> Dict[str, str]:
    source = dict(os.environ) if extra is None else dict(extra)
    return {key: value for key, value in source.items() if not _is_sensitive_env_key(key)}


def _write_file_atomically(path: str, data: bytes, mode: int) -> None:
    parent = str(Path(path).parent)
    fd, tmp = tempfile.mkstemp(prefix=".ark-write-", dir=parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as output:
            fd = -1
            output.write(data)
        os.replace(tmp, path)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.remove(tmp)
        except FileNotFoundError:
            pass


class _BoundedOutput:
    _MARKER = b"\n... truncated ..."

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._data = bytearray()
        self._truncated = False
        self._lock = threading.Lock()

    def append(self, chunk: bytes) -> None:
        with self._lock:
            remaining = max(0, self._limit - len(self._MARKER) - len(self._data))
            if remaining > 0:
                self._data.extend(chunk[:remaining])
            if len(chunk) > remaining:
                self._truncated = True

    def text(self) -> str:
        with self._lock:
            text = bytes(self._data).decode("utf-8", errors="replace")
            if self._truncated:
                text += self._MARKER.decode("ascii")
            return text


def _drain_output(stream: Any, output: _BoundedOutput) -> None:
    if stream is None:
        return
    try:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                return
            output.append(chunk)
    finally:
        stream.close()


def _kill_process(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, AttributeError):
        proc.kill()
