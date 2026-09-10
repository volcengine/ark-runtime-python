# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import os
import random
import socket
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import httpx

from .._exceptions import ArkAPIError
from .envinit import Initializer, InitializerOptions
from .session_tool_runner import SessionToolRunner, SessionToolRunnerOptions
from .tool_result_store import FileToolResultStore
from .tools import Tool, ToolContext, ToolSet, default_toolset
from .types import (
    DEFAULT_HEARTBEAT_SECONDS,
    DEFAULT_MAX_IDLE_SECONDS,
    EXPECTED_LAST_HEARTBEAT_NO_HEARTBEAT,
    WORK_STATE_STOPPED,
    WORK_STATE_STOPPING,
    APIError,
    IdleTimeout,
    SessionTerminated,
    WorkItem,
    is_fatal_4xx,
    is_status,
    work_session_id,
)

DEFAULT_POLL_BLOCK_MS = 999
POLL_BACKOFF_CAP_SECONDS = 60.0
_POLLER_TRANSIENT_ERRORS = (httpx.HTTPError, ArkAPIError, APIError)


@dataclass
class WorkPollerOptions:
    environment_id: str
    worker_id: str = ""
    block_ms: Optional[int] = DEFAULT_POLL_BLOCK_MS
    reclaim_older_than_ms: int = 0
    drain: bool = False
    auto_stop: bool = True
    stop_event: Optional[threading.Event] = None
    logger: logging.Logger = logging.getLogger("arkruntime.selfhosted.work_poller")


class WorkPoller:
    """Serial work poller with optional ownership cleanup.

    ``auto_stop`` is intended for iterator-style serial processing. Callers
    dispatching work concurrently must disable it and own heartbeat and stop.
    """

    def __init__(self, api: Any, options: WorkPollerOptions) -> None:
        if api is None:
            raise ValueError("api is required")
        if not options.environment_id:
            raise ValueError("environment_id is required")
        if not options.worker_id:
            options.worker_id = default_worker_id()
        self.api = api
        self.options = options
        self.current: Optional[WorkItem] = None
        self.error: Optional[BaseException] = None
        self.closed = False
        self._pending_stop = None
        self._failures = 0
        self._discards = 0

    def close(self) -> None:
        self.closed = True
        self._run_pending_stop()

    def next(self) -> Optional[WorkItem]:
        self._run_pending_stop()
        if self._is_closed():
            return None
        while not self._is_closed():
            try:
                item = self.api.poll_work(
                    self.options.environment_id,
                    worker_id=self.options.worker_id,
                    block_ms=self.options.block_ms,
                    reclaim_older_than_ms=self.options.reclaim_older_than_ms,
                )
            except _POLLER_TRANSIENT_ERRORS as exc:
                if _is_poller_fatal_4xx(exc):
                    self.error = exc
                    return None
                self._failures += 1
                sleep_seconds = _backoff(self._failures) + _jitter(0, 1)
                self.options.logger.warning("poll work failed err=%s sleep=%.3fs", exc, sleep_seconds)
                self._sleep(sleep_seconds)
                continue
            self._failures = 0
            if item is None or not item.id:
                if self.options.drain:
                    return None
                self._sleep(_jitter(1, 3))
                continue
            if not item.environment_id:
                item.environment_id = self.options.environment_id
            if not work_session_id(item):
                self.options.logger.warning(
                    "discard invalid work work_id=%s reason=missing session id",
                    item.id,
                )
                self._discard_invalid_work(item)
                continue
            try:
                self.api.ack_work(item.environment_id, item.id, worker_id=self.options.worker_id)
            except _POLLER_TRANSIENT_ERRORS as exc:
                self.options.logger.warning("ack work failed work_id=%s err=%s", item.id, exc)
                if _is_poller_fatal_4xx(exc):
                    self._stop_item(item, force=True)
                    continue
                self._backoff_discard()
                continue
            self.current = item
            if self.options.auto_stop:
                self._pending_stop = lambda item=item: self._stop_item(item, force=False)
            self._discards = 0
            self.options.logger.info(
                "claimed work work_id=%s session_id=%s",
                item.id,
                work_session_id(item),
            )
            return item
        return None

    def _run_pending_stop(self) -> None:
        pending = self._pending_stop
        self._pending_stop = None
        self.current = None
        if pending is not None:
            pending()

    def _discard_invalid_work(self, item: WorkItem) -> None:
        try:
            self.api.ack_work(item.environment_id, item.id, worker_id=self.options.worker_id)
        except Exception as exc:  # noqa: BLE001 - invalid work still obeys ACK ownership.
            self.options.logger.warning("ack invalid work failed work_id=%s err=%s", item.id, exc)
            return
        self._stop_item(item, force=True)
        self._backoff_discard()

    def _stop_item(self, item: WorkItem, *, force: bool) -> None:
        try:
            self.api.stop_work(item.environment_id, item.id, force=force)
        except Exception as exc:  # noqa: BLE001
            if not _is_resolved_status(exc):
                self.options.logger.warning("stop work failed work_id=%s err=%s", item.id, exc)

    def _backoff_discard(self) -> None:
        self._discards += 1
        self._sleep(_backoff(self._discards) + _jitter(0, 1))

    def _is_closed(self) -> bool:
        return self.closed or bool(self.options.stop_event and self.options.stop_event.is_set())

    def _sleep(self, seconds: float) -> None:
        if self.options.stop_event is not None:
            self.options.stop_event.wait(max(seconds, 0))
            return
        time.sleep(max(seconds, 0))


@dataclass
class HandleItemOptions:
    work_id: str = ""
    environment_id: str = ""
    session_id: str = ""
    latest_heartbeat_at: str = ""


@dataclass
class _ClaimedWork:
    id: str
    environment_id: str
    session_id: str
    latest_heartbeat_at: str = ""


@dataclass
class EnvironmentWorkerOptions:
    environment_id: str = ""
    worker_id: str = ""
    workdir: str = "."
    unrestricted_paths: bool = False
    tool_context: Optional[ToolContext] = None
    tools: Optional[ToolSet] = None
    max_idle_seconds: Optional[float] = DEFAULT_MAX_IDLE_SECONDS
    custom_tools: Dict[str, Tool] = field(default_factory=dict)
    logger: logging.Logger = logging.getLogger("arkruntime.selfhosted.environment_worker")
    tool_timeout_seconds: Optional[float] = None


class EnvironmentWorker:
    def __init__(self, api: Any, options: EnvironmentWorkerOptions) -> None:
        if api is None:
            raise ValueError("api is required")
        if not options.worker_id:
            options.worker_id = default_worker_id()
        self.api = api
        self.options = options
        self._stop = threading.Event()

    def close(self) -> None:
        self._stop.set()

    def run(self) -> None:
        if not self.options.environment_id:
            raise ValueError("environment_id is required")
        poller = WorkPoller(
            self.api,
            WorkPollerOptions(
                environment_id=self.options.environment_id,
                worker_id=self.options.worker_id,
                auto_stop=False,
                stop_event=self._stop,
                logger=self.options.logger,
            ),
        )
        try:
            while not self._stop.is_set():
                item = poller.next()
                if item is None:
                    if poller.error is not None:
                        raise poller.error
                    return
                try:
                    self._handle_item(_claimed_work_from_item(item))
                except (IdleTimeout, SessionTerminated):
                    pass
                except Exception as exc:  # noqa: BLE001 - continue polling after a bad work item.
                    self.options.logger.warning("handle work failed: %s", exc)
        finally:
            poller.close()

    def handle_item(self, options: HandleItemOptions) -> None:
        work = self._claimed_work_from_options(options)
        try:
            self._handle_item(work)
        except (IdleTimeout, SessionTerminated):
            return

    def _handle_item(self, work: _ClaimedWork) -> None:
        if not work.environment_id:
            work.environment_id = self.options.environment_id or os.environ.get("MA_ENVIRONMENT_ID", "")
        heartbeat_stop = threading.Event()
        work_stop = _CombinedStopEvent(self._stop, heartbeat_stop)
        heartbeat_done = threading.Event()
        heartbeat_cause = {"value": ""}
        heartbeat = None
        initializer = None
        try:
            workdir = self._workdir()
            heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                args=(work, heartbeat_stop, heartbeat_done, heartbeat_cause),
                daemon=True,
            )
            heartbeat_thread.start()
            heartbeat = heartbeat_thread
            session = self.api.get_session(work.session_id)
            if work_stop.is_set():
                return
            if session is None:
                raise ValueError("session response is empty")
            if not session.id:
                session.id = work.session_id
            initializer = Initializer(
                self.api,
                InitializerOptions(workdir=workdir, logger=self.options.logger),
            )
            initializer.setup(session)
            if work_stop.is_set():
                return
            tool_context = self._tool_context(workdir, work_stop)
            store = FileToolResultStore(workdir, work.session_id)
            runner = SessionToolRunner(
                self.api,
                work.session_id,
                SessionToolRunnerOptions(
                    work_id=work.id,
                    tools=self.options.tools or default_toolset(),
                    tool_context=tool_context,
                    custom_tools=self.options.custom_tools,
                    result_store=store,
                    max_idle_seconds=self.options.max_idle_seconds,
                    tool_timeout_seconds=self.options.tool_timeout_seconds,
                    stop_event=work_stop,
                    logger=self.options.logger,
                ),
            )
            runner.run()
        finally:
            if initializer is not None:
                try:
                    initializer.cleanup()
                except OSError as exc:
                    self.options.logger.warning("cleanup session skills failed: %s", exc)
            heartbeat_stop.set()
            if heartbeat is not None:
                heartbeat_done.wait(timeout=DEFAULT_HEARTBEAT_SECONDS + 1)
            cause = heartbeat_cause["value"]
            if _should_stop_item(cause):
                try:
                    self.api.stop_work(work.environment_id, work.id, force=True)
                except Exception as exc:  # noqa: BLE001
                    if not _is_resolved_status(exc):
                        self.options.logger.warning("stop work failed: %s", exc)
            else:
                self.options.logger.info(
                    "skip stop work after heartbeat ownership became uncertain cause=%s",
                    cause,
                )

    def _heartbeat_loop(self, work: _ClaimedWork, stop: threading.Event, done: threading.Event, cause: dict) -> None:
        interval = max(1.0, min(DEFAULT_HEARTBEAT_SECONDS / 2, DEFAULT_HEARTBEAT_SECONDS))
        ttl = DEFAULT_HEARTBEAT_SECONDS
        last = work.latest_heartbeat_at or EXPECTED_LAST_HEARTBEAT_NO_HEARTBEAT
        last_success = time.monotonic()
        try:
            while not stop.is_set():
                try:
                    resp = self.api.heartbeat_work(
                        work.environment_id,
                        work.id,
                        expected_last_heartbeat=last,
                        desired_ttl_seconds=int(ttl),
                    )
                except Exception as exc:  # noqa: BLE001
                    if is_status(exc, 412):
                        cause["value"] = "lease_lost"
                        stop.set()
                        return
                    if is_fatal_4xx(exc):
                        cause["value"] = "heartbeat_permanent_failure"
                        stop.set()
                        return
                    if time.monotonic() - last_success > ttl:
                        cause["value"] = "heartbeat_lost"
                        stop.set()
                        return
                    self.options.logger.warning(
                        "heartbeat failed work_id=%s session_id=%s since_last_success=%.3fs ttl=%.3fs err=%s",
                        work.id,
                        work.session_id,
                        time.monotonic() - last_success,
                        ttl,
                        exc,
                    )
                    stop.wait(interval)
                    continue
                if resp is None:
                    if time.monotonic() - last_success > ttl:
                        cause["value"] = "heartbeat_lost"
                        stop.set()
                        return
                    self.options.logger.warning(
                        "heartbeat empty response work_id=%s session_id=%s",
                        work.id,
                        work.session_id,
                    )
                    stop.wait(interval)
                    continue
                last_success = time.monotonic()
                if resp.last_heartbeat:
                    last = resp.last_heartbeat
                if resp.ttl_seconds > 0:
                    ttl = float(resp.ttl_seconds)
                    interval = max(1.0, min(ttl / 2, DEFAULT_HEARTBEAT_SECONDS))
                if resp.state in (WORK_STATE_STOPPING, WORK_STATE_STOPPED):
                    cause["value"] = "stop_requested"
                    stop.set()
                    return
                if resp.lease_extended is False:
                    cause["value"] = "lease_not_extended"
                    stop.set()
                    return
                stop.wait(interval)
        finally:
            done.set()

    def _tool_context(self, workdir: str, cancel_event: Any) -> ToolContext:
        base = self.options.tool_context or ToolContext(workdir=workdir)
        env = None if base.env is None else dict(base.env)
        tool_timeout_seconds = base.tool_timeout_seconds
        if self.options.tool_timeout_seconds is not None and self.options.tool_timeout_seconds > 0:
            tool_timeout_seconds = self.options.tool_timeout_seconds
        return ToolContext(
            workdir=workdir,
            env=env,
            unrestricted_paths=self.options.unrestricted_paths or base.unrestricted_paths,
            tool_timeout_seconds=tool_timeout_seconds,
            cancel_event=cancel_event,
        )

    def _workdir(self) -> str:
        """Return the shared worker workdir used for tool cwd and installed skills."""
        root = str(Path(self.options.workdir or ".").resolve())
        Path(root).mkdir(parents=True, exist_ok=True)
        return root

    def _claimed_work_from_options(self, options: HandleItemOptions) -> _ClaimedWork:
        work_id = options.work_id or os.environ.get("MA_WORK_ID", "")
        environment_id = options.environment_id or os.environ.get("MA_ENVIRONMENT_ID", "")
        session_id = options.session_id or os.environ.get("MA_SESSION_ID", "")
        latest_heartbeat = options.latest_heartbeat_at or os.environ.get("MA_LATEST_HEARTBEAT_AT", "")
        if not work_id:
            raise ValueError("work id is required")
        if not environment_id:
            raise ValueError("environment id is required")
        if not session_id:
            raise ValueError("session id is required")
        return _ClaimedWork(
            id=work_id,
            environment_id=environment_id,
            session_id=session_id,
            latest_heartbeat_at=latest_heartbeat,
        )


def _claimed_work_from_item(item: WorkItem) -> _ClaimedWork:
    session_id = work_session_id(item)
    if not item.id:
        raise ValueError("work item id must not be empty")
    if not session_id:
        raise ValueError("work item does not contain session id")
    return _ClaimedWork(
        id=item.id,
        environment_id=item.environment_id,
        session_id=session_id,
        latest_heartbeat_at=item.latest_heartbeat_at or "",
    )


def default_worker_id() -> str:
    return f"{socket.gethostname()}-{uuid4().hex[:12]}"


def _backoff(failures: int) -> float:
    value = min(POLL_BACKOFF_CAP_SECONDS, 2 ** max(failures, 1))
    return float(value)


def _is_poller_fatal_4xx(exc: BaseException) -> bool:
    if isinstance(exc, APIError):
        status_code = exc.status_code
    elif isinstance(exc, ArkAPIError) and hasattr(exc, "status_code"):
        status_code = int(exc.status_code)
    else:
        return False
    return 400 <= status_code < 500 and status_code not in (408, 409, 429)


def _is_resolved_status(exc: BaseException) -> bool:
    return is_status(exc, 404) or is_status(exc, 409) or is_status(exc, 412)


def _should_stop_item(heartbeat_cause: str) -> bool:
    return heartbeat_cause not in {
        "lease_lost",
        "lease_not_extended",
        "heartbeat_lost",
        "heartbeat_permanent_failure",
    }


class _CombinedStopEvent:
    def __init__(self, *events: threading.Event) -> None:
        self._events = events

    def is_set(self) -> bool:
        return any(event.is_set() for event in self._events)

    def wait(self, timeout: Optional[float] = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + max(timeout, 0)
        while not self.is_set():
            if deadline is not None and time.monotonic() >= deadline:
                return False
            time.sleep(0.05)
        return True


def _jitter(low: float, high: float) -> float:
    if high <= low:
        return max(high, 0)
    return low + random.random() * (high - low)
