# SPDX-License-Identifier: Apache-2.0
#
# Hand-written typed session-stream envelope + variant classes. Modeled
# on Go's sdks/go/arkruntime/model/session/session_stream_shim.go — kept
# in lockstep so callers moving between languages see the same
# ManagedAgents* names and the same per-variant field surface.
#
# The SSE stream endpoints on /sessions/:id/events/stream and
# /threads/:id/stream ship a heterogeneous wire union of 20+ event
# variants (agent.message / span.outcome_evaluation_end /
# session.status_idle / …). datamodel-code-generator can only emit a
# single generic ``ManagedAgentsSessionEvent(type: str, id, processed_at)``
# envelope — the concrete variants live here.
#
# Consumption pattern — plain Python isinstance dispatch:
#
#     for frame in client.sessions.events.stream(session_id):
#         ev = frame.data
#         if isinstance(ev, ManagedAgentsAgentMessageEvent):
#             for block in ev.content:
#                 if block.text:
#                     print(block.text)
#         elif isinstance(ev, ManagedAgentsSessionStatusIdleEvent):
#             break
#         elif isinstance(ev, ManagedAgentsSessionErrorEvent):
#             print("stream error:", ev.error.message)
#             break
#
# Any wire event not in the dispatch table below falls through to
# :class:`ManagedAgentsUnknownSessionEvent` — that lets the SDK stay
# forwards-compatible against server upgrades.
#
# Preserved across codegen regen via Makefile's
# ``--exclude='*_shim.py'`` rsync rule.

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type

from pydantic import model_validator

from arkruntime._models import BaseModel


class _DictCompatModel(BaseModel):
    """Base for shim models that accept legacy ``obj["field"]`` /
    ``obj.get("field")`` calls from callers written before the typed
    refactor. New callers should use attribute access.
    """

    def __getitem__(self, key: str) -> Any:
        if not hasattr(self, key):
            raise KeyError(key)
        return getattr(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class _SessionEventBase(_DictCompatModel):
    """Common envelope fields every wire event carries. Subclasses add
    variant-specific fields on top.
    """

    type: str
    id: str = ""
    processed_at: str = ""


# ---- Nested payload helpers (shared across variants) ----------------------


class ManagedAgentsStopReason(_DictCompatModel):
    """Categorizes why a session or thread went idle. Common values:
    ``end_turn`` / ``retries_exhausted`` / ``user_interrupt``.
    """

    type: str = ""


class ManagedAgentsRetryStatus(_DictCompatModel):
    """Optionally accompanies a session error to hint whether the runtime
    plans to retry. Common values: ``exhausted`` / ``pending`` / ``in_progress``.
    """

    type: str = ""


class ManagedAgentsSessionErrorPayload(_DictCompatModel):
    """The ``error`` field on ``session.error`` /
    ``session.thread_status_terminated`` frames.
    """

    type: str = ""
    message: str = ""
    retry_status: Optional[ManagedAgentsRetryStatus] = None


class ManagedAgentsModelUsage(_DictCompatModel):
    """Emitted on ``span.model_request_end`` and
    ``span.outcome_evaluation_end`` frames to report token accounting.
    """

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class ManagedAgentsOutputContentBlock(_DictCompatModel):
    """Content-list element carried by ``user.message`` / ``agent.message`` /
    ``agent.thinking`` / ``agent.tool_result`` frames. Fields overlap across
    block types — dispatch on ``.type == 'text' | 'image' | 'document'``
    in caller code.
    """

    type: str = ""
    text: str = ""
    source: Any = None
    title: str = ""
    context: str = ""


# ---- Session-lifecycle events ---------------------------------------------


class ManagedAgentsSessionStatusRunningEvent(_SessionEventBase):
    """Session has an in-flight turn. Fires at the start of every
    send-events → agent-loop round.
    """


class ManagedAgentsSessionStatusIdleEvent(_SessionEventBase):
    """Session finished a turn and is ready for more input. ``stop_reason``
    indicates whether the turn ended normally (``end_turn``) or hit a bail-out.
    """

    stop_reason: Optional[ManagedAgentsStopReason] = None


class ManagedAgentsSessionStatusTerminatedEvent(_SessionEventBase):
    """Session was terminated (client delete or server-side kill). No
    further events will fire.
    """

    stop_reason: Optional[ManagedAgentsStopReason] = None


class ManagedAgentsSessionErrorEvent(_SessionEventBase):
    """Runtime hit an unrecoverable error mid-turn (model provider down,
    tool crashed, etc.).
    """

    error: ManagedAgentsSessionErrorPayload = ManagedAgentsSessionErrorPayload()


# ---- Thread-lifecycle events ----------------------------------------------


class ManagedAgentsSessionThreadCreatedEvent(_SessionEventBase):
    """A sub-agent thread was spawned (either the primary thread on first
    turn or a sub-agent delegation).
    """

    session_thread_id: str = ""
    agent_name: str = ""
    parent_thread_id: str = ""


class ManagedAgentsSessionThreadStatusRunningEvent(_SessionEventBase):
    session_thread_id: str = ""
    agent_name: str = ""


class ManagedAgentsSessionThreadStatusIdleEvent(_SessionEventBase):
    session_thread_id: str = ""
    agent_name: str = ""
    stop_reason: Optional[ManagedAgentsStopReason] = None


class ManagedAgentsSessionThreadStatusTerminatedEvent(_SessionEventBase):
    session_thread_id: str = ""
    agent_name: str = ""
    stop_reason: Optional[ManagedAgentsStopReason] = None


# ---- User-side echo events -------------------------------------------------


class ManagedAgentsUserMessageEvent(_SessionEventBase):
    """Server's echo of a ``user.message`` input event pushed via
    SendSessionEvents.
    """

    session_thread_id: str = ""
    content: List[ManagedAgentsOutputContentBlock] = []


class ManagedAgentsUserDefineOutcomeEvent(_SessionEventBase):
    """Echo of a ``user.define_outcome`` input event."""

    outcome_id: str = ""
    description: str = ""
    max_iterations: int = 0
    rubric: Any = None


class ManagedAgentsUserInterruptEvent(_SessionEventBase):
    """Echo of a ``user.interrupt`` input event."""

    session_thread_id: str = ""
    reason: str = ""


class ManagedAgentsUserToolConfirmationEvent(_SessionEventBase):
    """Echo of a ``user.tool_confirmation`` input event."""

    session_thread_id: str = ""
    tool_use_id: str = ""
    result: str = ""
    deny_message: str = ""
    turn_id: str = ""


# ---- Agent output events ---------------------------------------------------


class ManagedAgentsAgentMessageEvent(_SessionEventBase):
    """Assistant's response. ``content`` is a list of typed blocks; the
    common case is a single ``{type:'text', text:'...'}`` block, but the
    agent may emit multiple.
    """

    session_thread_id: str = ""
    content: List[ManagedAgentsOutputContentBlock] = []


class ManagedAgentsAgentThinkingEvent(_SessionEventBase):
    """Assistant's internal deliberation frame. ``content`` may be empty or
    carry a thinking-mode summary block.
    """

    session_thread_id: str = ""
    content: List[ManagedAgentsOutputContentBlock] = []


class ManagedAgentsAgentToolUseEvent(_SessionEventBase):
    """Agent invoked a tool. ``input`` is the tool's argument object
    (schema per tool).
    """

    session_thread_id: str = ""
    tool_use_id: str = ""
    name: str = ""
    input: Any = None


class ManagedAgentsAgentToolResultEvent(_SessionEventBase):
    """Tool's result (post ``user.tool_result`` if the tool required
    client-side execution, or runtime-owned if it was a builtin/MCP tool).
    """

    session_thread_id: str = ""
    tool_use_id: str = ""
    content: List[ManagedAgentsOutputContentBlock] = []
    is_error: bool = False


class ManagedAgentsAgentMCPToolUseEvent(_SessionEventBase):
    """Agent invoked an MCP tool (registered via a Vault credential).
    Distinct wire event from ``agent.tool_use`` to signal the extra
    ``mcp_server_name`` routing metadata.
    """

    session_thread_id: str = ""
    tool_use_id: str = ""
    mcp_server_name: str = ""
    name: str = ""
    input: Any = None


class ManagedAgentsAgentMCPToolResultEvent(_SessionEventBase):
    """Result of an MCP tool invocation. Same shape as
    ``agent.tool_result`` but on the MCP path.
    """

    session_thread_id: str = ""
    tool_use_id: str = ""
    mcp_server_name: str = ""
    content: List[ManagedAgentsOutputContentBlock] = []
    is_error: bool = False


class ManagedAgentsAgentThreadContextCompactedEvent(_SessionEventBase):
    """Runtime summarized an older section of thread history to fit under
    the token budget. Subsequent turns run against the compacted context.
    """

    session_thread_id: str = ""
    summary: str = ""


# ---- Cross-thread relay events --------------------------------------------


class ManagedAgentsAgentThreadMessageSentEvent(_SessionEventBase):
    """Coordinator agent sent a delegation prompt to a sub-agent thread
    (multiagent).
    """

    from_session_thread_id: str = ""
    to_session_thread_id: str = ""


class ManagedAgentsAgentThreadMessageReceivedEvent(_SessionEventBase):
    """Sub-agent received a coordinator's delegation prompt (multiagent)."""

    from_session_thread_id: str = ""
    to_session_thread_id: str = ""


# ---- Span (observability) events ------------------------------------------


class ManagedAgentsSpanModelRequestStartEvent(_SessionEventBase):
    """A model provider call was about to be issued. Pair with the matching
    end event.
    """

    session_thread_id: str = ""


class ManagedAgentsSpanModelRequestEndEvent(_SessionEventBase):
    """A model provider call completed (success or error). ``model_usage``
    reports token accounting.
    """

    session_thread_id: str = ""
    model_request_start_id: str = ""
    model_usage: Optional[ManagedAgentsModelUsage] = None
    is_error: bool = False
    error_message: str = ""


class ManagedAgentsSpanOutcomeEvaluationStartEvent(_SessionEventBase):
    """Runtime kicked off grading a completed iteration against the user's
    rubric.
    """

    iteration: int = 0
    outcome_id: str = ""


class ManagedAgentsSpanOutcomeEvaluationOngoingEvent(_SessionEventBase):
    """Periodic progress while the grader is running."""

    outcome_id: str = ""


class ManagedAgentsSpanOutcomeEvaluationEndEvent(_SessionEventBase):
    """Grader verdict for one iteration. Common ``result`` values:
    ``satisfied`` / ``needs_revision`` / ``max_iterations_reached`` /
    ``failed`` / ``interrupted``.
    """

    iteration: int = 0
    outcome_evaluation_start_id: str = ""
    outcome_id: str = ""
    result: str = ""
    explanation: str = ""
    usage: Optional[ManagedAgentsModelUsage] = None


# ---- Fallback -------------------------------------------------------------


class ManagedAgentsUnknownSessionEvent(_SessionEventBase):
    """Yielded for wire events this SDK version doesn't have a typed
    variant for yet. Preserves the untouched JSON payload in
    ``raw_payload`` so callers can json.loads it into their own shape.
    """

    raw_payload: str = ""


# ---- Decoder dispatch -----------------------------------------------------


_EVENT_TYPE_MAP: Dict[str, Type[_SessionEventBase]] = {
    "session.status_running": ManagedAgentsSessionStatusRunningEvent,
    "session.status_idle": ManagedAgentsSessionStatusIdleEvent,
    "session.status_terminated": ManagedAgentsSessionStatusTerminatedEvent,
    "session.error": ManagedAgentsSessionErrorEvent,
    "session.thread_created": ManagedAgentsSessionThreadCreatedEvent,
    "session.thread_status_running": ManagedAgentsSessionThreadStatusRunningEvent,
    "session.thread_status_idle": ManagedAgentsSessionThreadStatusIdleEvent,
    "session.thread_status_terminated": ManagedAgentsSessionThreadStatusTerminatedEvent,
    "user.message": ManagedAgentsUserMessageEvent,
    "user.define_outcome": ManagedAgentsUserDefineOutcomeEvent,
    "user.interrupt": ManagedAgentsUserInterruptEvent,
    "user.tool_confirmation": ManagedAgentsUserToolConfirmationEvent,
    "agent.message": ManagedAgentsAgentMessageEvent,
    "agent.thinking": ManagedAgentsAgentThinkingEvent,
    "agent.tool_use": ManagedAgentsAgentToolUseEvent,
    "agent.tool_result": ManagedAgentsAgentToolResultEvent,
    "agent.mcp_tool_use": ManagedAgentsAgentMCPToolUseEvent,
    "agent.mcp_tool_result": ManagedAgentsAgentMCPToolResultEvent,
    "agent.thread_context_compacted": ManagedAgentsAgentThreadContextCompactedEvent,
    "agent.thread_message_sent": ManagedAgentsAgentThreadMessageSentEvent,
    "agent.thread_message_received": ManagedAgentsAgentThreadMessageReceivedEvent,
    "span.model_request_start": ManagedAgentsSpanModelRequestStartEvent,
    "span.model_request_end": ManagedAgentsSpanModelRequestEndEvent,
    "span.outcome_evaluation_start": ManagedAgentsSpanOutcomeEvaluationStartEvent,
    "span.outcome_evaluation_ongoing": ManagedAgentsSpanOutcomeEvaluationOngoingEvent,
    "span.outcome_evaluation_end": ManagedAgentsSpanOutcomeEvaluationEndEvent,
}


def decode_session_event(raw: Any) -> _SessionEventBase:
    """Parse a raw SSE data payload into the concrete typed variant
    matching its ``type`` discriminator. Unknown / malformed payloads
    become :class:`ManagedAgentsUnknownSessionEvent` with the raw bytes
    preserved.

    Accepts either the raw JSON string (as emitted by the SSE decoder)
    or an already-parsed dict.
    """
    if raw is None or raw == "":
        return ManagedAgentsUnknownSessionEvent(type="", raw_payload="")

    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")

    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
        except ValueError:
            return ManagedAgentsUnknownSessionEvent(type="", raw_payload=raw)
    elif isinstance(raw, dict):
        obj = raw
    else:
        return ManagedAgentsUnknownSessionEvent(type="", raw_payload=str(raw))

    if not isinstance(obj, dict):
        return ManagedAgentsUnknownSessionEvent(
            type="",
            raw_payload=raw if isinstance(raw, str) else json.dumps(obj),
        )

    typ = obj.get("type", "") or ""
    cls = _EVENT_TYPE_MAP.get(typ)
    if cls is None:
        return ManagedAgentsUnknownSessionEvent(
            type=typ,
            id=obj.get("id", "") or "",
            processed_at=obj.get("processed_at", "") or "",
            raw_payload=raw if isinstance(raw, str) else json.dumps(obj),
        )
    try:
        return cls.model_validate(obj)
    except Exception:
        return ManagedAgentsUnknownSessionEvent(
            type=typ,
            id=obj.get("id", "") or "",
            processed_at=obj.get("processed_at", "") or "",
            raw_payload=raw if isinstance(raw, str) else json.dumps(obj),
        )


# ---- Stream event envelope -----------------------------------------------


class SessionStreamEvent(_DictCompatModel):
    """A single decoded SSE frame from
    :meth:`client.sessions.events.stream` /
    :meth:`client.sessions.threads.stream`.

    ``type`` is the effective event discriminator (SSE ``event:`` line
    first, JSON ``type`` field second). ``data`` is a concrete
    ``ManagedAgents*Event`` instance (or :class:`ManagedAgentsUnknownSessionEvent`
    fallback). Dispatch happens in :func:`decode_session_event`, and
    ``data`` is intentionally typed as ``Any`` to sidestep pydantic's
    union-matching heuristic — which otherwise picks the first
    structurally-compatible variant and mis-tags every event.

    Backward-compat: ``frame["event"]`` returns ``.type``;
    ``frame["data"]`` returns the JSON string of
    ``.data.model_dump()``. Legacy callers that consumed the pre-typed
    dict shape keep working.
    """

    type: str = ""
    data: Any = None

    def __getitem__(self, key: str) -> Any:
        if key == "event":
            return self.type
        if key == "data":
            payload = self.data
            if hasattr(payload, "model_dump"):
                payload = payload.model_dump()
            return json.dumps(payload, ensure_ascii=False)
        return super().__getitem__(key)


# ---- Typed ListSessionEvents response ------------------------------------


class ListSessionEventsResponse(_DictCompatModel):
    """User-facing shape for the ``GET /sessions/:id/events`` list
    endpoint. The codegen ``ListSessionEventsResponseWire`` types
    ``data`` as ``List[Dict[str, object]]`` — we accept the same wire
    payload here but dispatch every dict through
    :func:`decode_session_event`, so :attr:`events` is a list of
    typed variant instances instead of raw dicts.

    Mirrors Go's ``session.ListSessionEventsResponse.Events`` on the
    Go SDK. ``next_page`` passes through unchanged.
    """

    events: List[Any] = []
    next_page: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def _decode_wire_events(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "events" in data and "data" not in data:
            # Already in the typed shape (e.g. from another SDK path).
            return data
        wire_events = data.get("data") or []
        typed: List[Any] = []
        for item in wire_events:
            if isinstance(item, dict):
                typed.append(decode_session_event(item))
            else:
                typed.append(item)
        return {"events": typed, "next_page": data.get("next_page")}
