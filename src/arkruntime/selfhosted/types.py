# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from arkruntime.types.environment import (
    HeartbeatWorkResponse,
    VolcTag,
    WorkState,
)
from arkruntime.types.environment import (
    WorkData as WorkData,
)
from arkruntime.types.environment import (
    WorkItem as WorkItem,
)

EVENT_TYPE_AGENT_TOOL_USE = "agent.tool_use"
EVENT_TYPE_AGENT_CUSTOM_TOOL_USE = "agent.custom_tool_use"
EVENT_TYPE_USER_TOOL_CONFIRMATION = "user.tool_confirmation"
EVENT_TYPE_USER_TOOL_RESULT = "user.tool_result"
EVENT_TYPE_USER_CUSTOM_TOOL_RESULT = "user.custom_tool_result"
EVENT_TYPE_SESSION_STATUS_IDLE = "session.status_idle"
EVENT_TYPE_SESSION_STATUS_RUNNING = "session.status_running"
EVENT_TYPE_SESSION_STATUS_RESCHEDULED = "session.status_rescheduled"
EVENT_TYPE_SESSION_STATUS_TERMINATED = "session.status_terminated"
EVENT_TYPE_SESSION_DELETED = "session.deleted"

PERMISSION_ALLOW = "allow"
PERMISSION_DENY = "deny"

CONFIRMATION_ALLOW = "allow"
CONFIRMATION_DENY = "deny"

EVENT_LIST_ORDER_ASC = "asc"
EVENT_LIST_ORDER_DESC = "desc"

SESSION_STOP_REASON_END_TURN = "end_turn"
SESSION_STOP_REASON_REQUIRES_ACTION = "requires_action"
SESSION_STOP_REASON_RETRIES_EXHAUSTED = "retries_exhausted"

WORK_STATE_QUEUED = WorkState.queued
WORK_STATE_STARTING = WorkState.starting
WORK_STATE_ACTIVE = WorkState.active
WORK_STATE_STOPPING = WorkState.stopping
WORK_STATE_STOPPED = WorkState.stopped

HeartbeatResponse = HeartbeatWorkResponse
WorkTag = VolcTag

EXPECTED_LAST_HEARTBEAT_NO_HEARTBEAT = "NO_HEARTBEAT"

WORKER_ERROR_KIND_AUTH = "auth"
WORKER_ERROR_KIND_PERMISSION = "permission"
WORKER_ERROR_KIND_LEASE_CONFLICT = "lease_conflict"
WORKER_ERROR_KIND_RATE_LIMIT = "rate_limit"
WORKER_ERROR_KIND_TIMEOUT = "timeout"
WORKER_ERROR_KIND_NETWORK = "network"
WORKER_ERROR_KIND_TOOL_ERROR = "tool_error"
WORKER_ERROR_KIND_INVALID_RESPONSE = "invalid_response"

DEFAULT_MAX_IDLE_SECONDS = 60.0
DEFAULT_TOOL_TIMEOUT_SECONDS = 120.0
DEFAULT_HEARTBEAT_SECONDS = 30.0


class EventStreamUnsupported(RuntimeError):
    """Raised when an API adapter does not support SSE event streaming."""


class SessionTerminated(RuntimeError):
    """Raised when the session was terminated by the control plane."""


class IdleTimeout(RuntimeError):
    """Raised after an end_turn idle event remains idle for max_idle."""


class APIError(RuntimeError):
    """Control-plane API error with HTTP status and request id."""

    def __init__(self, status_code: int, message: str, request_id: str = "") -> None:
        super().__init__(f"worker api status {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.request_id = request_id


class WorkerError(RuntimeError):
    """Stable worker error classification for callers."""

    def __init__(
        self,
        kind: str,
        message: str,
        *,
        request_id: str = "",
        retryable: bool = False,
        cause: Optional[BaseException] = None,
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.request_id = request_id
        self.retryable = retryable
        self.__cause__ = cause


def is_status(exc: BaseException, status_code: int) -> bool:
    return isinstance(exc, APIError) and exc.status_code == status_code


def is_fatal_4xx(exc: BaseException) -> bool:
    return isinstance(exc, APIError) and 400 <= exc.status_code < 500 and exc.status_code not in (408, 409, 412, 429)


def classify_worker_error(exc: BaseException) -> WorkerError:
    if isinstance(exc, WorkerError):
        return exc
    kind = WORKER_ERROR_KIND_NETWORK
    retryable = True
    request_id = ""
    if isinstance(exc, TimeoutError):
        kind = WORKER_ERROR_KIND_TIMEOUT
    if isinstance(exc, APIError):
        request_id = exc.request_id
        retryable = False
        if exc.status_code == 401:
            kind = WORKER_ERROR_KIND_AUTH
        elif exc.status_code == 403:
            kind = WORKER_ERROR_KIND_PERMISSION
        elif exc.status_code in (409, 412):
            kind = WORKER_ERROR_KIND_LEASE_CONFLICT
        elif exc.status_code == 408:
            kind = WORKER_ERROR_KIND_TIMEOUT
            retryable = True
        elif exc.status_code == 429:
            kind = WORKER_ERROR_KIND_RATE_LIMIT
            retryable = True
        elif exc.status_code >= 500:
            kind = WORKER_ERROR_KIND_NETWORK
            retryable = True
        else:
            kind = WORKER_ERROR_KIND_INVALID_RESPONSE
    return WorkerError(kind, str(exc), request_id=request_id, retryable=retryable, cause=exc)


def work_session_id(item: WorkItem) -> str:
    if item.data.id and (not item.data.type or item.data.type == "session"):
        return item.data.id
    return ""


@dataclass
class SkillRef:
    name: str = ""
    display_name: str = ""
    id: str = ""
    skill_id: str = ""
    type: str = ""
    version: str = ""
    download_url: str = ""

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "SkillRef":
        return cls(
            name=str(raw.get("name") or ""),
            display_name=str(raw.get("display_name") or ""),
            id=str(raw.get("id") or ""),
            skill_id=str(raw.get("skill_id") or ""),
            type=str(raw.get("type") or ""),
            version=str(raw.get("version") or ""),
            download_url=str(raw.get("download_url") or ""),
        )

    def id_value(self) -> str:
        return self.skill_id or self.id

    def name_value(self) -> str:
        return self.name or self.display_name or self.id_value()


@dataclass
class AgentConfig:
    skills: List[SkillRef] = field(default_factory=list)


@dataclass
class Session:
    id: str
    agent: AgentConfig = field(default_factory=AgentConfig)
    skills: List[SkillRef] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "Session":
        agent_raw = raw.get("agent") if isinstance(raw.get("agent"), Mapping) else {}
        return cls(
            id=str(raw.get("id") or ""),
            agent=AgentConfig(skills=_skill_refs(agent_raw.get("skills") or [])),
            skills=_skill_refs(raw.get("skills") or []),
            raw=dict(raw),
        )

    def skill_refs(self) -> List[SkillRef]:
        return self.skills or self.agent.skills


@dataclass
class ContentBlock:
    type: str
    text: str = ""
    media_type: str = ""
    data: Any = None
    source: Any = None
    title: str = ""
    context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"type": self.type}
        if self.type == "text" or self.text:
            out["text"] = self.text
        if self.media_type:
            out["media_type"] = self.media_type
        if self.data is not None:
            out["data"] = self.data
        if self.source is not None:
            out["source"] = self.source
        if self.title:
            out["title"] = self.title
        if self.context:
            out["context"] = self.context
        return out


@dataclass
class Event:
    type: str
    id: str = ""
    name: str = ""
    input: Any = None
    processed_at: str = ""
    evaluated_permission: str = ""
    session_thread_id: str = ""
    tool_use_id: str = ""
    custom_tool_use_id: str = ""
    result: str = ""
    deny_message: str = ""
    stop_reason: Any = None
    content: List[ContentBlock] = field(default_factory=list)
    is_error: Optional[bool] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "Event":
        known = {
            "id",
            "type",
            "name",
            "input",
            "processed_at",
            "evaluated_permission",
            "session_thread_id",
            "tool_use_id",
            "custom_tool_use_id",
            "result",
            "deny_message",
            "stop_reason",
            "content",
            "is_error",
        }
        content = []
        for block in raw.get("content") or []:
            if isinstance(block, Mapping):
                content.append(
                    ContentBlock(
                        type=str(block.get("type") or ""),
                        text=str(block.get("text") or ""),
                        media_type=str(block.get("media_type") or ""),
                        data=block.get("data"),
                        source=block.get("source"),
                        title=str(block.get("title") or ""),
                        context=str(block.get("context") or ""),
                    )
                )
        return cls(
            id=str(raw.get("id") or ""),
            type=str(raw.get("type") or ""),
            name=str(raw.get("name") or ""),
            input=raw.get("input"),
            processed_at=str(raw.get("processed_at") or ""),
            evaluated_permission=str(raw.get("evaluated_permission") or ""),
            session_thread_id=str(raw.get("session_thread_id") or ""),
            tool_use_id=str(raw.get("tool_use_id") or ""),
            custom_tool_use_id=str(raw.get("custom_tool_use_id") or ""),
            result=str(raw.get("result") or ""),
            deny_message=str(raw.get("deny_message") or ""),
            stop_reason=raw.get("stop_reason"),
            content=content,
            is_error=raw.get("is_error") if isinstance(raw.get("is_error"), bool) else None,
            extra={k: v for k, v in raw.items() if k not in known},
        )

    def stop_reason_type(self) -> str:
        if isinstance(self.stop_reason, Mapping):
            return str(self.stop_reason.get("type") or "")
        if isinstance(self.stop_reason, str):
            return self.stop_reason
        return ""

    def stop_reason_event_ids(self) -> List[str]:
        if not isinstance(self.stop_reason, Mapping):
            return []
        event_ids = self.stop_reason.get("event_ids")
        if not isinstance(event_ids, list):
            return []
        return [str(event_id) for event_id in event_ids if event_id]

    def to_dict(self) -> Dict[str, Any]:
        out = dict(self.extra)
        out.update(
            {
                "id": self.id,
                "type": self.type,
                "processed_at": self.processed_at,
            }
        )
        for key in (
            "name",
            "evaluated_permission",
            "session_thread_id",
            "tool_use_id",
            "custom_tool_use_id",
            "result",
            "deny_message",
        ):
            value = getattr(self, key)
            if value:
                out[key] = value
        if self.input is not None:
            out["input"] = self.input
        if self.stop_reason is not None:
            out["stop_reason"] = self.stop_reason
        if self.content:
            out["content"] = [block.to_dict() for block in self.content]
        if self.is_error is not None:
            out["is_error"] = self.is_error
        return {k: v for k, v in out.items() if v is not None and v != ""}


@dataclass
class ListEventsResponse:
    events: List[Event] = field(default_factory=list)
    next_page: str = ""


@dataclass
class SkillContent:
    body: Any
    content_length: int = -1
    file_name: str = ""
    content_type: str = ""


@dataclass
class ToolCallResult:
    tool_use_id: str
    name: str
    custom: bool
    confirmation: str = ""
    posted: bool = False
    event: Optional[Event] = None
    result: Optional[Event] = None


def new_event_id(prefix: str = "evt") -> str:
    return f"{prefix}-{secrets.token_hex(8)}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_user_tool_result_event(
    tool_use_id: str,
    content: Iterable[ContentBlock],
    is_error: bool,
    thread_id: str = "",
) -> Event:
    return Event(
        id=new_event_id("evt"),
        type=EVENT_TYPE_USER_TOOL_RESULT,
        tool_use_id=tool_use_id,
        content=list(content),
        is_error=is_error,
        processed_at=utc_now_iso(),
        session_thread_id=thread_id,
    )


def new_user_custom_tool_result_event(
    custom_tool_use_id: str,
    content: Iterable[ContentBlock],
    is_error: bool,
    thread_id: str = "",
) -> Event:
    return Event(
        id=new_event_id("evt"),
        type=EVENT_TYPE_USER_CUSTOM_TOOL_RESULT,
        custom_tool_use_id=custom_tool_use_id,
        content=list(content),
        is_error=is_error,
        processed_at=utc_now_iso(),
        session_thread_id=thread_id,
    )


def tool_confirmation_call_id(event: Event) -> str:
    return event.tool_use_id or event.custom_tool_use_id


def tool_use_call_id(event: Event) -> str:
    return event.tool_use_id or event.custom_tool_use_id or event.id


def tool_result_call_id(event: Event) -> str:
    return event.tool_use_id or event.custom_tool_use_id


def _skill_refs(raw: Iterable[Any]) -> List[SkillRef]:
    out: List[SkillRef] = []
    for item in raw:
        if isinstance(item, Mapping):
            out.append(SkillRef.from_mapping(item))
    return out
