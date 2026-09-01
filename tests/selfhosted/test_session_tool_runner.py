# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import threading
import time

import pytest

from arkruntime.selfhosted import Event, ListEventsResponse, SessionToolRunner, SessionToolRunnerOptions
from arkruntime.selfhosted.tools import FunctionTool, ToolContext, ToolSet, text_result


class _ListAPI:
    def __init__(self) -> None:
        self.calls = 0
        self.created_at_values = []
        self.sent = []
        self.sent_event = threading.Event()

    def list_events(self, session_id, **kwargs):
        self.calls += 1
        self.created_at_values.append(kwargs.get("created_at_gt"))
        if self.calls == 1:
            raise RuntimeError("temporary list failure")
        return ListEventsResponse(
            events=[
                Event(
                    id="event-1",
                    type="agent.custom_tool_use",
                    name="custom",
                    custom_tool_use_id="call-1",
                    session_thread_id="thread-1",
                    input={},
                )
            ]
        )

    def send_event(self, session_id, event):
        self.sent.append(event)
        self.sent_event.set()


def test_list_fallback_retries_full_history_and_converts_custom_tool_error(tmp_path) -> None:
    api = _ListAPI()

    def fail(_input, _context):
        raise RuntimeError("custom tool failed")

    runner = SessionToolRunner(
        api,
        "session-1",
        SessionToolRunnerOptions(
            tools=ToolSet(),
            tool_context=ToolContext(workdir=str(tmp_path)),
            custom_tools={"custom": FunctionTool("custom", fail)},
            prefer_stream=False,
            event_poll_interval_seconds=0.01,
        ),
    )
    thread = threading.Thread(target=runner.run)
    thread.start()
    assert api.sent_event.wait(2)
    runner.close()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert api.calls >= 2
    assert all(value is None for value in api.created_at_values)
    assert len(api.sent) == 1
    assert api.sent[0].is_error is True
    assert api.sent[0].content[0].text == "custom tool failed"


def test_runner_requires_tool_context() -> None:
    with pytest.raises(ValueError, match="tool context"):
        SessionToolRunner(object(), "session-1", SessionToolRunnerOptions(tools=ToolSet()))


def test_confirmed_tool_is_released_once_when_post_fails(tmp_path) -> None:
    executions = []

    def execute(_input, _context):
        executions.append(True)
        return ToolSet().execute("missing", {}, _context)

    runner = SessionToolRunner(
        object(),
        "session-1",
        SessionToolRunnerOptions(
            tools=ToolSet([FunctionTool("count", execute)]),
            tool_context=ToolContext(workdir=str(tmp_path)),
        ),
    )
    tool_use = Event(
        id="event-tool-use",
        type="agent.tool_use",
        name="count",
        tool_use_id="call-1",
        evaluated_permission="ask",
        input={},
    )
    confirmation = Event(type="user.tool_confirmation", tool_use_id="call-1", result="allow")
    runner._state.pending_ask["call-1"] = tool_use
    runner._state.confirmations["call-1"] = confirmation
    runner._state.retry_send_event = lambda _event, _call_id: False

    runner._state.release_confirmed_tool_uses()
    runner._state.release_confirmed_tool_uses()

    assert len(executions) == 1
    assert "call-1" not in runner._state.pending_ask


def test_duplicate_stream_idle_event_does_not_reset_idle_deadline(tmp_path) -> None:
    runner = SessionToolRunner(
        object(),
        "session-1",
        SessionToolRunnerOptions(tools=ToolSet(), tool_context=ToolContext(workdir=str(tmp_path))),
    )
    event = Event(
        id="idle-1",
        type="session.status_idle",
        stop_reason={"type": "end_turn"},
    )

    runner._state.handle_stream_event(event)
    armed_at = runner._state.idle_armed_at
    time.sleep(0.001)
    runner._state.handle_stream_event(event)

    assert runner._state.idle_armed_at == armed_at


def test_reconcile_does_not_reset_idle_deadline_for_seen_history(tmp_path) -> None:
    runner = SessionToolRunner(
        object(),
        "session-1",
        SessionToolRunnerOptions(tools=ToolSet(), tool_context=ToolContext(workdir=str(tmp_path))),
    )
    event = Event(
        id="idle-1",
        type="session.status_idle",
        stop_reason={"type": "end_turn"},
    )

    runner._state.process_listed_events([event], reconcile=True)
    armed_at = runner._state.idle_armed_at
    time.sleep(0.001)
    runner._state.process_listed_events([event], reconcile=True)

    assert runner._state.idle_armed_at == armed_at


@pytest.mark.parametrize("override, expected", [(None, 7), (0, 7), (-1, 7), (3, 3)])
def test_tool_execution_copies_context_and_preserves_configured_timeout(tmp_path, override, expected) -> None:
    contexts = []

    def capture(_input, context):
        contexts.append(context)
        return ToolSet().execute("missing", {}, context)

    original = ToolContext(workdir=str(tmp_path), tool_timeout_seconds=7)
    runner = SessionToolRunner(
        object(),
        "session-1",
        SessionToolRunnerOptions(
            tools=ToolSet([FunctionTool("capture", capture)]),
            tool_context=original,
            tool_timeout_seconds=override,
        ),
    )
    event = Event(id="tool-1", type="agent.tool_use", name="capture", tool_use_id="call-1", input={})

    runner._state.execute_tool(event, custom=False)

    assert contexts[0] is not original
    assert contexts[0].tool_timeout_seconds == expected
    assert original.tool_timeout_seconds == 7


@pytest.mark.parametrize("custom", [False, True])
def test_tool_timeout_abandons_noncooperative_tool(tmp_path, custom) -> None:
    release = threading.Event()
    started = threading.Event()

    def block(_input, _context):
        started.set()
        release.wait(2)
        return text_result("late")

    tool = FunctionTool("blocking", block)
    runner = SessionToolRunner(
        object(),
        "session-1",
        SessionToolRunnerOptions(
            tools=ToolSet() if custom else ToolSet([tool]),
            tool_context=ToolContext(workdir=str(tmp_path)),
            custom_tools={"blocking": tool} if custom else {},
            tool_timeout_seconds=0.02,
        ),
    )
    event = Event(id="tool-1", type="agent.tool_use", name="blocking", tool_use_id="call-1", input={})

    started_at = time.monotonic()
    try:
        result = runner._state.execute_tool(event, custom=custom)
    finally:
        release.set()

    assert started.wait(1)
    assert time.monotonic() - started_at < 0.5
    assert result.is_error is True
    assert result.content[0].text == "tool execution timed out after 0.02s"


def test_successful_send_stays_answered_when_mark_sent_fails(tmp_path, caplog) -> None:
    class FailingStore:
        def mark_sent(self, _call_id):
            raise OSError("ledger unavailable")

    runner = SessionToolRunner(
        object(),
        "session-1",
        SessionToolRunnerOptions(
            tools=ToolSet(),
            tool_context=ToolContext(workdir=str(tmp_path)),
            result_store=FailingStore(),
        ),
    )
    source = Event(id="tool-1", type="agent.tool_use", name="bash", tool_use_id="call-1")
    result = Event(id="result-1", type="user.tool_result", tool_use_id="call-1")
    runner._state.pending_results["call-1"] = result
    runner._state.retry_send_event = lambda _event, _call_id: True

    with caplog.at_level("WARNING"):
        runner._state.send_result("call-1", source, False, "", result)

    assert runner._state.answered["call-1"] is True
    assert "call-1" not in runner._state.pending_results
    assert "mark tool result sent failed" in caplog.text
