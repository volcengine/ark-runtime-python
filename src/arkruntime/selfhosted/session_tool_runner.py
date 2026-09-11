# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import queue
import random
import threading
import time
from dataclasses import dataclass, field, replace
from typing import Any, Dict, Iterable, List, Optional, Set

from .tool_result_store import FileToolResultStore
from .tools import Tool, ToolContext, ToolResult, ToolSet, error_result
from .types import (
    CONFIRMATION_ALLOW,
    CONFIRMATION_DENY,
    DEFAULT_MAX_IDLE_SECONDS,
    DEFAULT_TOOL_TIMEOUT_SECONDS,
    EVENT_LIST_ORDER_ASC,
    EVENT_TYPE_AGENT_CUSTOM_TOOL_USE,
    EVENT_TYPE_AGENT_TOOL_USE,
    EVENT_TYPE_SESSION_DELETED,
    EVENT_TYPE_SESSION_STATUS_IDLE,
    EVENT_TYPE_SESSION_STATUS_RESCHEDULED,
    EVENT_TYPE_SESSION_STATUS_RUNNING,
    EVENT_TYPE_SESSION_STATUS_TERMINATED,
    EVENT_TYPE_USER_CUSTOM_TOOL_RESULT,
    EVENT_TYPE_USER_TOOL_CONFIRMATION,
    EVENT_TYPE_USER_TOOL_RESULT,
    PERMISSION_ALLOW,
    PERMISSION_DENY,
    SESSION_STOP_REASON_END_TURN,
    SESSION_STOP_REASON_REQUIRES_ACTION,
    ContentBlock,
    Event,
    EventStreamUnsupported,
    IdleTimeout,
    SessionTerminated,
    ToolCallResult,
    is_fatal_4xx,
    new_user_custom_tool_result_event,
    new_user_tool_result_event,
    tool_confirmation_call_id,
    tool_result_call_id,
    tool_use_call_id,
)

STREAM_BACKOFF_START = 0.5
STREAM_BACKOFF_CAP = 10.0
STREAM_HEALTHY_AFTER = 30.0
SEND_RETRIES = 3
STREAM_QUEUE_SIZE = 256


class _ToolCancelEvent:
    def __init__(self, parent: Any = None) -> None:
        self._parent = parent
        self._local = threading.Event()

    def set(self) -> None:
        self._local.set()

    def is_set(self) -> bool:
        return self._local.is_set() or bool(self._parent and self._parent.is_set())

    def wait(self, timeout: Optional[float] = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + max(timeout, 0)
        while not self.is_set():
            wait_for = 0.05
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return self.is_set()
                wait_for = min(wait_for, remaining)
            self._local.wait(wait_for)
        return True


@dataclass
class SessionToolRunnerOptions:
    work_id: str = ""
    tools: ToolSet = None  # type: ignore[assignment]
    tool_context: ToolContext = None  # type: ignore[assignment]
    custom_tools: Dict[str, Tool] = field(default_factory=dict)
    result_store: Optional[FileToolResultStore] = None
    event_page: str = ""
    event_poll_interval_seconds: float = 0.5
    event_limit: int = 100
    max_idle_seconds: Optional[float] = DEFAULT_MAX_IDLE_SECONDS
    tool_timeout_seconds: Optional[float] = None
    send_timeout_seconds: float = 15.0
    prefer_stream: bool = True
    stream_timeout_seconds: float = 30.0
    stop_event: Any = None
    logger: logging.Logger = logging.getLogger("arkruntime.selfhosted.session_tool_runner")
    on_tool_error: Any = None


class SessionToolRunner:
    def __init__(self, api: Any, session_id: str, options: SessionToolRunnerOptions) -> None:
        if not session_id:
            raise ValueError("session id must not be empty")
        if api is None:
            raise ValueError("session tool runner api must not be empty")
        if options is None:
            raise ValueError("session tool runner options must not be empty")
        if options.tools is None:
            raise ValueError("session tool runner tools must not be empty")
        if options.tool_context is None:
            raise ValueError("session tool runner tool context must not be empty")
        self.api = api
        self.session_id = session_id
        self.options = options
        self._stop = threading.Event()
        self._results: List[ToolCallResult] = []
        self._state = _RunnerState(self)

    @property
    def results(self) -> List[ToolCallResult]:
        return self._results

    def close(self) -> None:
        self._stop.set()

    def _is_stopped(self) -> bool:
        return self._stop.is_set() or bool(self.options.stop_event and self.options.stop_event.is_set())

    def run(self) -> List[ToolCallResult]:
        if self.options.result_store is not None:
            pending, processed = self.options.result_store.recover()
            self._state.pending_results.update(pending)
            self._state.recovered_results.update(pending)
            self._state.processed.update(processed)
            self._state.answered.update(processed)
        if self.options.prefer_stream and hasattr(self.api, "stream_events"):
            try:
                self._consume_stream_loop()
                return self._results
            except EventStreamUnsupported:
                pass
            except (IdleTimeout, SessionTerminated):
                raise
            except Exception:
                if self._is_stopped():
                    return self._results
                raise
        self._consume_list()
        return self._results

    def _consume_stream_loop(self) -> None:
        backoff = STREAM_BACKOFF_START
        while not self._is_stopped():
            event_queue: "queue.Queue[object]" = queue.Queue(maxsize=STREAM_QUEUE_SIZE)
            opened_at = time.monotonic()
            pump = threading.Thread(target=self._pump_stream, args=(event_queue,), daemon=True)
            pump.start()
            self._state.reconcile()
            while not self._is_stopped() and (pump.is_alive() or not event_queue.empty()):
                self._state.flush_results()
                self._raise_if_idle_expired()
                try:
                    item = event_queue.get(timeout=self._state.next_wait_seconds(0.5))
                except queue.Empty:
                    continue
                if isinstance(item, BaseException):
                    if time.monotonic() - opened_at > STREAM_HEALTHY_AFTER:
                        backoff = STREAM_BACKOFF_START
                    if isinstance(item, EventStreamUnsupported):
                        raise item
                    if is_fatal_4xx(item):
                        raise item
                    break
                self._state.handle_stream_event(item)  # type: ignore[arg-type]
            self._sleep_or_idle(_jitter(backoff))
            backoff = min(backoff * 2, STREAM_BACKOFF_CAP)

    def _pump_stream(self, event_queue: "queue.Queue[object]") -> None:
        stream = None
        try:
            stream = self.api.stream_events(self.session_id, timeout=self.options.stream_timeout_seconds)
            for event in stream:
                if self._is_stopped() or not self._put_stream_item(event_queue, event):
                    return
        except Exception as exc:  # noqa: BLE001 - forwarded to the owner loop.
            self._put_stream_item(event_queue, exc)
        finally:
            close = getattr(stream, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:  # noqa: BLE001 - stream may already be closing in its pump thread.
                    pass

    def _put_stream_item(self, event_queue: "queue.Queue[object]", item: object) -> bool:
        while not self._is_stopped():
            try:
                event_queue.put(item, timeout=0.1)
                return True
            except queue.Full:
                continue
        return False

    def _consume_list(self) -> None:
        while not self._is_stopped():
            self._state.reconcile(reconcile=False)
            self._state.flush_results()
            self._raise_if_idle_expired()
            self._sleep_or_idle(self.options.event_poll_interval_seconds)

    def _sleep_or_idle(self, seconds: float) -> None:
        deadline = time.monotonic() + max(seconds, 0)
        while not self._is_stopped():
            self._raise_if_idle_expired()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            wait_for = self._state.next_wait_seconds(min(remaining, 0.5))
            if self.options.stop_event is not None:
                self.options.stop_event.wait(wait_for)
            else:
                self._stop.wait(wait_for)

    def _raise_if_idle_expired(self) -> None:
        if self._state.idle_expired():
            raise IdleTimeout("session idle after end_turn")


class _RunnerState:
    def __init__(self, runner: SessionToolRunner) -> None:
        self.runner = runner
        self.page = runner.options.event_page
        self.processed: Dict[str, bool] = {}
        self.seen: Dict[str, bool] = {}
        self.answered: Dict[str, bool] = {}
        self.pending_results: Dict[str, Event] = {}
        self.recovered_results: Set[str] = set()
        self.pending_ask: Dict[str, Event] = {}
        self.confirmations: Dict[str, Event] = {}
        self.external_tools: Dict[str, Event] = {}
        self.session_tool_uses: Set[str] = set()
        self.tool_uses_since_status: Set[str] = set()
        self.blocking_event_ids: Set[str] = set()
        self.blocking_events_known = False
        self.idle_armed_at = 0.0
        self.idle_arm_pending = False

    def reconcile(self, *, reconcile: bool = True) -> None:
        backoff = STREAM_BACKOFF_START
        while not self.runner._is_stopped():
            try:
                self._reconcile_once(reconcile=reconcile)
                return
            except Exception as exc:  # noqa: BLE001 - runner owns retry classification.
                if is_fatal_4xx(exc):
                    raise
                self.runner.options.logger.warning(
                    "reconcile list events failed err=%s sleep=%.3fs",
                    exc,
                    backoff,
                )
                self.runner._sleep_or_idle(_jitter(backoff))
                backoff = min(backoff * 2, STREAM_BACKOFF_CAP)

    def _reconcile_once(self, *, reconcile: bool) -> None:
        events: List[Event] = []
        page = ""
        while not self.runner._is_stopped():
            resp = self.runner.api.list_events(
                self.runner.session_id,
                page=page,
                limit=min(max(self.runner.options.event_limit, 1), 1000),
                order=EVENT_LIST_ORDER_ASC,
            )
            if resp is None:
                break
            events.extend(resp.events)
            if not resp.next_page:
                break
            page = resp.next_page
        self.process_listed_events(events, reconcile=reconcile)

    def process_listed_events(self, events: Iterable[Event], reconcile: bool = False) -> None:
        pending: List[Event] = []
        pending_ids: Dict[str, bool] = {}
        touched_idle = False
        last_was_end_turn = False
        for event in events:
            seen_now = self.mark_event_seen(event)
            if not reconcile and not seen_now:
                continue
            self.observe_session_state(event)
            if seen_now and event.type != EVENT_TYPE_USER_TOOL_CONFIRMATION:
                touched_idle = True
                last_was_end_turn = (
                    event.type == EVENT_TYPE_SESSION_STATUS_IDLE
                    and event.stop_reason_type() == SESSION_STOP_REASON_END_TURN
                )
            if event.type == EVENT_TYPE_USER_TOOL_CONFIRMATION:
                self.record_confirmation(event)
            elif event.type in (EVENT_TYPE_USER_TOOL_RESULT, EVENT_TYPE_USER_CUSTOM_TOOL_RESULT):
                self.mark_answered(tool_result_call_id(event))
            elif event.type in (EVENT_TYPE_AGENT_TOOL_USE, EVENT_TYPE_AGENT_CUSTOM_TOOL_USE):
                call_id = tool_use_call_id(event)
                if call_id and not pending_ids.get(call_id):
                    pending.append(event)
                    pending_ids[call_id] = True
            elif event.type in (EVENT_TYPE_SESSION_STATUS_TERMINATED, EVENT_TYPE_SESSION_DELETED):
                raise SessionTerminated("session terminated")
        self.reconcile_recovered_results()
        if touched_idle:
            self.disarm_idle()
        for event in pending:
            call_id = tool_use_call_id(event)
            if self.is_answered(call_id) or not self.should_handle_tool_use(call_id):
                continue
            self.handle_tool_use(event, event.type == EVENT_TYPE_AGENT_CUSTOM_TOOL_USE)
        self.release_confirmed_tool_uses()
        if touched_idle and last_was_end_turn:
            if self.has_unblocked_outstanding_tool(pending):
                self.disarm_idle()
            else:
                self.arm_idle()

    def note_idle_event(self, event: Event) -> None:
        if event.type == EVENT_TYPE_USER_TOOL_CONFIRMATION:
            return
        if event.type == EVENT_TYPE_SESSION_STATUS_IDLE and event.stop_reason_type() == SESSION_STOP_REASON_END_TURN:
            self.arm_idle()
            return
        self.disarm_idle()

    def handle_stream_event(self, event: Event) -> None:
        if not self.mark_event_seen(event):
            return
        self.observe_session_state(event)
        self.reconcile_recovered_results()
        self.note_idle_event(event)
        self.handle_event(event)

    def handle_event(self, event: Event) -> None:
        if event.type == EVENT_TYPE_USER_TOOL_CONFIRMATION:
            self.record_confirmation(event)
            self.release_confirmed_tool_uses()
        elif event.type in (EVENT_TYPE_USER_TOOL_RESULT, EVENT_TYPE_USER_CUSTOM_TOOL_RESULT):
            self.mark_answered(tool_result_call_id(event))
        elif event.type in (EVENT_TYPE_AGENT_TOOL_USE, EVENT_TYPE_AGENT_CUSTOM_TOOL_USE):
            self.handle_tool_use(event, event.type == EVENT_TYPE_AGENT_CUSTOM_TOOL_USE)
        elif event.type in (EVENT_TYPE_SESSION_STATUS_TERMINATED, EVENT_TYPE_SESSION_DELETED):
            raise SessionTerminated("session terminated")

    def mark_event_seen(self, event: Event) -> bool:
        key = event.id or tool_use_call_id(event)
        if not key:
            return True
        if self.seen.get(key):
            return False
        self.seen[key] = True
        return True

    def mark_answered(self, call_id: str) -> None:
        if not call_id:
            return
        self.answered[call_id] = True
        self.processed[call_id] = True
        self.pending_results.pop(call_id, None)
        self.recovered_results.discard(call_id)
        self.pending_ask.pop(call_id, None)
        self.external_tools.pop(call_id, None)
        self.maybe_arm_pending_idle()

    def is_answered(self, call_id: str) -> bool:
        return bool(call_id and self.answered.get(call_id))

    def record_confirmation(self, event: Event) -> None:
        call_id = tool_confirmation_call_id(event)
        if call_id and not self.is_answered(call_id):
            self.confirmations[call_id] = event

    def release_confirmed_tool_uses(self) -> None:
        ready = [event for call_id, event in self.pending_ask.items() if call_id in self.confirmations]
        for event in ready:
            self.pending_ask.pop(tool_use_call_id(event), None)
            self.handle_tool_use(event, event.type == EVENT_TYPE_AGENT_CUSTOM_TOOL_USE)

    def has_unblocked_outstanding_tool(self, pending: Iterable[Event]) -> bool:
        for event in pending:
            call_id = tool_use_call_id(event)
            if not call_id or self.is_answered(call_id) or not self.should_handle_tool_use(call_id):
                continue
            if call_id in self.pending_ask or call_id in self.pending_results:
                continue
            return True
        return False

    def handle_tool_use(self, event: Event, custom: bool) -> None:
        call_id = tool_use_call_id(event)
        if not call_id or self.is_answered(call_id):
            return
        pending = self.pending_results.get(call_id)
        if pending is not None:
            if call_id in self.recovered_results:
                return
            self.send_result(call_id, event, custom, "", pending)
            return
        if not self.owns_tool(event, custom):
            self.external_tools[call_id] = event
            self.maybe_arm_pending_idle()
            self.runner._results.append(ToolCallResult(call_id, event.name, custom, posted=False, event=event))
            return
        confirmation, allowed = self.permission_allows(event, custom, call_id)
        if not allowed:
            self.runner._results.append(
                ToolCallResult(call_id, event.name, custom, confirmation=confirmation, posted=False, event=event)
            )
            return
        if self.runner.options.result_store is not None:
            decision = self.runner.options.result_store.begin(call_id, event)
            if decision.sent:
                self.mark_answered(call_id)
                return
            if decision.result is not None:
                self.pending_results[call_id] = decision.result
                self.send_result(call_id, event, custom, "", decision.result)
                return
        result = self.execute_tool(event, custom)
        self.post_result(event, custom, call_id, result, confirmation)

    def owns_tool(self, event: Event, custom: bool) -> bool:
        if custom:
            return event.name in self.runner.options.custom_tools
        return self.runner.options.tools.has(event.name)

    def permission_allows(self, event: Event, custom: bool, call_id: str) -> tuple:
        if custom:
            return "", True
        permission = event.evaluated_permission
        if permission in ("", PERMISSION_ALLOW):
            return "", True
        if permission == "ask":
            confirmation = self.confirmations.get(call_id)
            if confirmation is None:
                self.pending_ask[call_id] = event
                return "", False
            if confirmation.result == CONFIRMATION_ALLOW:
                return CONFIRMATION_ALLOW, True
            self.mark_answered(call_id)
            return CONFIRMATION_DENY, False
        if permission == PERMISSION_DENY:
            self.mark_answered(call_id)
            return CONFIRMATION_DENY, False
        self.pending_ask[call_id] = event
        return "", False

    def execute_tool(self, event: Event, custom: bool) -> ToolResult:
        context = replace(self.runner.options.tool_context)
        if self.runner.options.tool_timeout_seconds is not None and self.runner.options.tool_timeout_seconds > 0:
            context.tool_timeout_seconds = self.runner.options.tool_timeout_seconds
        if context.tool_timeout_seconds <= 0:
            context.tool_timeout_seconds = DEFAULT_TOOL_TIMEOUT_SECONDS
        cancel_event = _ToolCancelEvent(context.cancel_event)
        context.cancel_event = cancel_event
        results: "queue.Queue[ToolResult]" = queue.Queue(maxsize=1)

        def execute() -> None:
            results.put(self._execute_tool(event, custom, context))

        thread = threading.Thread(target=execute, name="ma-self-host-tool", daemon=True)
        thread.start()
        deadline = time.monotonic() + context.tool_timeout_seconds
        while True:
            if self.runner._is_stopped() or cancel_event.is_set():
                cancel_event.set()
                return error_result("tool execution canceled")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                try:
                    return results.get_nowait()
                except queue.Empty:
                    cancel_event.set()
                    return error_result(f"tool execution timed out after {context.tool_timeout_seconds:g}s")
            try:
                return results.get(timeout=min(remaining, 0.05))
            except queue.Empty:
                continue

    def _execute_tool(self, event: Event, custom: bool, context: ToolContext) -> ToolResult:
        if custom:
            tool = self.runner.options.custom_tools[event.name]
            try:
                return tool.execute(event.input, context)
            except Exception as exc:  # noqa: BLE001 - custom tool failures become tool results.
                return error_result(str(exc))
        return self.runner.options.tools.execute(event.name, event.input, context)

    def post_result(self, event: Event, custom: bool, call_id: str, result: ToolResult, confirmation: str) -> None:
        blocks = list(result.content)
        if custom:
            out = new_user_custom_tool_result_event(call_id, blocks, result.is_error, event.session_thread_id)
        else:
            out = new_user_tool_result_event(call_id, blocks, result.is_error, event.session_thread_id)
        if self.runner.options.result_store is not None:
            try:
                self.runner.options.result_store.save_result(call_id, out)
            except Exception as exc:  # noqa: BLE001 - delivery must continue after local ledger failure.
                self.runner.options.logger.warning(
                    "persist tool result failed tool_use_id=%s err=%s",
                    call_id,
                    exc,
                )
            self.pending_results[call_id] = out
        self.send_result(call_id, event, custom, confirmation, out)

    def send_result(self, call_id: str, event: Event, custom: bool, confirmation: str, out: Event) -> None:
        posted = self.retry_send_event(out, call_id)
        if posted:
            self.mark_answered(call_id)
            if self.runner.options.result_store is not None:
                try:
                    self.runner.options.result_store.mark_sent(call_id)
                except Exception as exc:  # noqa: BLE001 - MA already accepted the result.
                    self.runner.options.logger.warning(
                        "mark tool result sent failed tool_use_id=%s event_id=%s err=%s",
                        call_id,
                        out.id,
                        exc,
                    )
        elif self.runner.options.result_store is not None:
            self.pending_results[call_id] = out
        self.runner._results.append(
            ToolCallResult(
                tool_use_id=call_id,
                name=event.name,
                custom=custom,
                confirmation=confirmation,
                posted=posted,
                event=event,
                result=out,
            )
        )

    def retry_send_event(self, event: Event, call_id: str) -> bool:
        last_exc: Optional[BaseException] = None
        for attempt in range(SEND_RETRIES):
            try:
                self.runner.api.send_event(self.runner.session_id, event)
                return True
            except Exception as exc:  # noqa: BLE001 - mirrors Go retry classification.
                last_exc = exc
                if is_fatal_4xx(exc) or self.runner._is_stopped():
                    break
                if attempt < SEND_RETRIES - 1:
                    self.runner._sleep_or_idle(attempt + 1)
        if self.runner.options.on_tool_error and last_exc is not None:
            self.runner.options.on_tool_error(event, last_exc)
        return False

    def flush_results(self) -> None:
        for call_id, event in list(self.pending_results.items()):
            if call_id in self.recovered_results:
                continue
            if self.retry_send_event(event, call_id):
                self.mark_answered(call_id)
                if self.runner.options.result_store is not None:
                    try:
                        self.runner.options.result_store.mark_sent(call_id)
                    except Exception as exc:  # noqa: BLE001 - MA already accepted the result.
                        self.runner.options.logger.warning(
                            "mark pending tool result sent failed tool_use_id=%s event_id=%s err=%s",
                            call_id,
                            event.id,
                            exc,
                        )
        self.maybe_arm_pending_idle()

    def observe_session_state(self, event: Event) -> None:
        if event.type in (EVENT_TYPE_AGENT_TOOL_USE, EVENT_TYPE_AGENT_CUSTOM_TOOL_USE):
            call_id = tool_use_call_id(event)
            if call_id:
                self.session_tool_uses.add(call_id)
                self.tool_uses_since_status.add(call_id)
            return
        if event.type == EVENT_TYPE_SESSION_STATUS_IDLE:
            self.blocking_events_known = True
            self.blocking_event_ids = set()
            if event.stop_reason_type() == SESSION_STOP_REASON_REQUIRES_ACTION:
                self.blocking_event_ids.update(event.stop_reason_event_ids())
            self.tool_uses_since_status.clear()
            return
        if event.type in (EVENT_TYPE_SESSION_STATUS_RUNNING, EVENT_TYPE_SESSION_STATUS_RESCHEDULED):
            self.blocking_events_known = True
            self.blocking_event_ids.clear()
            self.tool_uses_since_status.clear()

    def should_handle_tool_use(self, call_id: str) -> bool:
        if not self.blocking_events_known:
            return True
        return call_id in self.blocking_event_ids or call_id in self.tool_uses_since_status

    def reconcile_recovered_results(self) -> None:
        if not self.blocking_events_known:
            return
        for call_id in list(self.recovered_results):
            if call_id in self.blocking_event_ids and call_id in self.session_tool_uses:
                self.recovered_results.discard(call_id)
                continue
            if call_id in self.tool_uses_since_status:
                continue
            self.recovered_results.discard(call_id)
            self.pending_results.pop(call_id, None)
            self.runner.options.logger.warning("discard stale recovered tool result tool_use_id=%s", call_id)
            if self.runner.options.result_store is not None:
                discard = getattr(self.runner.options.result_store, "discard", None)
                if not callable(discard):
                    continue
                try:
                    discard(call_id)
                except Exception as exc:  # noqa: BLE001 - optional custom store cleanup must not stop the runner.
                    self.runner.options.logger.warning(
                        "discard persisted tool result failed tool_use_id=%s err=%s", call_id, exc
                    )
        self.maybe_arm_pending_idle()

    def arm_idle(self) -> None:
        if not self.max_idle_seconds():
            return
        if self.has_idle_blockers():
            self.idle_arm_pending = True
            self.idle_armed_at = 0.0
            return
        self.idle_arm_pending = False
        self.idle_armed_at = time.monotonic()

    def disarm_idle(self) -> None:
        self.idle_arm_pending = False
        self.idle_armed_at = 0.0

    def maybe_arm_pending_idle(self) -> None:
        if self.idle_arm_pending and not self.has_idle_blockers():
            self.idle_arm_pending = False
            self.idle_armed_at = time.monotonic()

    def has_idle_blockers(self) -> bool:
        return bool(self.pending_ask or self.pending_results or self.external_tools)

    def idle_expired(self) -> bool:
        max_idle = self.max_idle_seconds()
        return bool(max_idle and self.idle_armed_at and time.monotonic() - self.idle_armed_at >= max_idle)

    def max_idle_seconds(self) -> float:
        if self.runner.options.max_idle_seconds is None:
            return 0.0
        return self.runner.options.max_idle_seconds

    def next_wait_seconds(self, fallback: float) -> float:
        if not self.idle_armed_at:
            return fallback
        remaining = self.max_idle_seconds() - (time.monotonic() - self.idle_armed_at)
        if remaining <= 0:
            return 0.001
        return max(0.001, min(fallback, remaining))


def _jitter(seconds: float) -> float:
    if seconds <= 0:
        return 0
    half = seconds / 2
    return half + random.random() * half


def result_content_blocks(result: ToolResult) -> List[ContentBlock]:
    return list(result.content)
