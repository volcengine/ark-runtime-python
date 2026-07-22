from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, Iterator, List, Union

import httpx

from ..._base_client import make_request_options
from ..._constants import CLIENT_REQUEST_HEADER
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, NotGiven
from ...types.session.managed_agents_event_params import ManagedAgentsEventParams
from ...types.session.send_session_events_response import SendSessionEventsResponse
from ...types.session.session_stream_shim import (
    ListSessionEventsResponse,
    SessionStreamEvent,
    decode_session_event,
)

__all__ = ["SessionEvents", "AsyncSessionEvents"]


def _raise_for_stream_status(resource: Any, resp: httpx.Response) -> None:
    """Translate a non-2xx SSE-open response into an ``ArkAPIStatusError``.

    The stream methods run their HTTP GET outside the base client's
    ``_request()`` path (so we get access to the raw response body as an
    SSE line iterator), which means ``resp.raise_for_status()`` would leak
    an ``httpx.HTTPStatusError`` to callers — inconsistent with every
    other SDK method that maps 404/401/etc. onto typed
    ``ArkNotFoundError``/``ArkAuthenticationError`` etc. This helper mirrors
    the base client's own error path so a caller catching ``ArkAPIError``
    covers streams too.
    """
    if resp.status_code < 400:
        return
    # Reading the body is safe here — httpx has already headers-only'd this
    # response, and the SSE stream we intended never began, so nothing else
    # will consume it.
    if not resp.is_closed:
        resp.read()
    request_id = resp.headers.get(CLIENT_REQUEST_HEADER, "")
    raise resource._client._make_status_error_from_response(resp, request_id=request_id) from None


async def _araise_for_stream_status(resource: Any, resp: httpx.Response) -> None:
    """Async variant of :func:`_raise_for_stream_status` — same contract,
    only differs in how the response body is drained.
    """
    if resp.status_code < 400:
        return
    if not resp.is_closed:
        await resp.aread()
    request_id = resp.headers.get(CLIENT_REQUEST_HEADER, "")
    raise resource._client._make_status_error_from_response(resp, request_id=request_id) from None


def _peek_event_type(event_name: str, data: str) -> str:
    """Resolve the effective SSE event type.

    The ark-managed-agents stream emits data-only frames (no explicit
    ``event:`` line); the type lives inside the JSON payload under the
    top-level ``type`` field. Prefer the explicit ``event:`` when
    present, otherwise peek the JSON. Non-JSON or type-less payloads
    fall through with an empty string.
    """
    if event_name:
        return event_name
    if not data or not data.startswith("{"):
        return ""
    try:
        obj = json.loads(data)
    except ValueError:
        return ""
    return obj.get("type", "") or "" if isinstance(obj, dict) else ""


def _decode_stream_frame(event_name: str, data: str) -> SessionStreamEvent:
    """Build a SessionStreamEvent from a decoded SSE frame. Runs the
    payload through :func:`decode_session_event` so ``.data`` is a
    concrete typed variant (``ManagedAgentsAgentMessageEvent`` /
    ``ManagedAgentsSpanOutcomeEvaluationEndEvent`` / …), not a raw dict.
    Empty or non-JSON payloads become
    :class:`ManagedAgentsUnknownSessionEvent` so callers can filter by
    ``event.type`` without special-casing malformed frames.
    """
    typ = _peek_event_type(event_name, data)
    typed = decode_session_event(data if data else "")
    if not typ and getattr(typed, "type", ""):
        typ = typed.type
    return SessionStreamEvent(type=typ, data=typed)


def _list_events_query(
    *,
    created_at_gt: Union[str, NotGiven] = NOT_GIVEN,
    created_at_gte: Union[str, NotGiven] = NOT_GIVEN,
    created_at_lt: Union[str, NotGiven] = NOT_GIVEN,
    created_at_lte: Union[str, NotGiven] = NOT_GIVEN,
    limit: Union[int, NotGiven] = NOT_GIVEN,
    order: Union[str, NotGiven] = NOT_GIVEN,
    page: Union[str, NotGiven] = NOT_GIVEN,
    types: Union[List[str], NotGiven] = NOT_GIVEN,
) -> Dict[str, Any]:
    """Assemble the query dict for List Session Events / List Thread Events.

    Field names & wire tags mirror the thrift IDL:
      - created_at[gt|gte|lt|lte] — RFC 3339 window bounds
      - limit / page / order / types — pagination + filter
    """
    q: Dict[str, Any] = {}
    if not isinstance(created_at_gt, NotGiven):
        q["created_at[gt]"] = created_at_gt
    if not isinstance(created_at_gte, NotGiven):
        q["created_at[gte]"] = created_at_gte
    if not isinstance(created_at_lt, NotGiven):
        q["created_at[lt]"] = created_at_lt
    if not isinstance(created_at_lte, NotGiven):
        q["created_at[lte]"] = created_at_lte
    if not isinstance(limit, NotGiven):
        q["limit"] = limit
    if not isinstance(order, NotGiven):
        q["order"] = order
    if not isinstance(page, NotGiven):
        q["page"] = page
    if not isinstance(types, NotGiven):
        q["types"] = types
    return q


class SessionEvents(SyncAPIResource):
    def send(
        self,
        session_id: str,
        *,
        events: List[ManagedAgentsEventParams],
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> SendSessionEventsResponse:
        if not session_id:
            raise ValueError("session_id is required")
        return self._post(
            f"/sessions/{session_id}/events",
            body=dump_body({"events": events}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SendSessionEventsResponse,
        )

    def list(
        self,
        session_id: str,
        *,
        created_at_gt: Union[str, NotGiven] = NOT_GIVEN,
        created_at_gte: Union[str, NotGiven] = NOT_GIVEN,
        created_at_lt: Union[str, NotGiven] = NOT_GIVEN,
        created_at_lte: Union[str, NotGiven] = NOT_GIVEN,
        limit: Union[int, NotGiven] = NOT_GIVEN,
        order: Union[str, NotGiven] = NOT_GIVEN,
        page: Union[str, NotGiven] = NOT_GIVEN,
        types: Union[List[str], NotGiven] = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListSessionEventsResponse:
        """List historical session events. Returns a
        :class:`ListSessionEventsResponse` whose ``.events`` list holds
        concrete ``ManagedAgents*Event`` instances (dispatched from the
        wire ``type`` discriminator via :func:`decode_session_event`)."""
        if not session_id:
            raise ValueError("session_id is required")
        query = _list_events_query(
            created_at_gt=created_at_gt,
            created_at_gte=created_at_gte,
            created_at_lt=created_at_lt,
            created_at_lte=created_at_lte,
            limit=limit,
            order=order,
            page=page,
            types=types,
        )
        merged_query: Dict[str, Any] = {**query, **(extra_query or {})}
        return self._get(
            f"/sessions/{session_id}/events",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=merged_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListSessionEventsResponse,
        )

    def stream(
        self,
        session_id: str,
        *,
        timeout: Union[float, None] = None,
    ) -> Iterator[SessionStreamEvent]:
        """Open the session's SSE event stream. Yields
        :class:`SessionStreamEvent` for each frame — ``event.type`` gives
        the wire event type (``agent.message`` / ``session.status_idle`` / …)
        and ``event.data`` is a concrete ``ManagedAgents*Event`` instance
        (dispatched via :func:`decode_session_event`). Caller iterates the
        returned generator; the underlying HTTP connection closes when
        the generator is exhausted or GC'd.
        """
        if not session_id:
            raise ValueError("session_id is required")
        client = self._client._client  # httpx.Client
        base = str(self._client._base_url).rstrip("/")
        url = f"{base}/sessions/{session_id}/events/stream"
        headers = {"Accept": "text/event-stream", **(self._client.auth_headers or {})}
        with client.stream("GET", url, headers=headers, timeout=timeout) as resp:
            _raise_for_stream_status(self, resp)
            event_name = ""
            data_buf: List[str] = []
            for raw_line in resp.iter_lines():
                if raw_line is None:
                    continue
                line = raw_line if isinstance(raw_line, str) else raw_line.decode("utf-8")
                if line == "":
                    if data_buf:
                        yield _decode_stream_frame(event_name, "\n".join(data_buf))
                    event_name = ""
                    data_buf = []
                    continue
                if line.startswith(":"):
                    continue
                name, _, value = line.partition(":")
                if value.startswith(" "):
                    value = value[1:]
                if name == "event":
                    event_name = value
                elif name == "data":
                    data_buf.append(value)


class AsyncSessionEvents(AsyncAPIResource):
    async def send(
        self,
        session_id: str,
        *,
        events: List[ManagedAgentsEventParams],
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> SendSessionEventsResponse:
        if not session_id:
            raise ValueError("session_id is required")
        return await self._post(
            f"/sessions/{session_id}/events",
            body=dump_body({"events": events}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SendSessionEventsResponse,
        )

    async def list(
        self,
        session_id: str,
        *,
        created_at_gt: Union[str, NotGiven] = NOT_GIVEN,
        created_at_gte: Union[str, NotGiven] = NOT_GIVEN,
        created_at_lt: Union[str, NotGiven] = NOT_GIVEN,
        created_at_lte: Union[str, NotGiven] = NOT_GIVEN,
        limit: Union[int, NotGiven] = NOT_GIVEN,
        order: Union[str, NotGiven] = NOT_GIVEN,
        page: Union[str, NotGiven] = NOT_GIVEN,
        types: Union[List[str], NotGiven] = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListSessionEventsResponse:
        """Async variant of list()."""
        if not session_id:
            raise ValueError("session_id is required")
        query = _list_events_query(
            created_at_gt=created_at_gt,
            created_at_gte=created_at_gte,
            created_at_lt=created_at_lt,
            created_at_lte=created_at_lte,
            limit=limit,
            order=order,
            page=page,
            types=types,
        )
        merged_query: Dict[str, Any] = {**query, **(extra_query or {})}
        return await self._get(
            f"/sessions/{session_id}/events",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=merged_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListSessionEventsResponse,
        )

    async def stream(
        self,
        session_id: str,
        *,
        timeout: Union[float, None] = None,
    ) -> AsyncIterator[SessionStreamEvent]:
        """Async variant of :meth:`SessionEvents.stream`. Yields
        :class:`SessionStreamEvent` for each SSE frame."""
        if not session_id:
            raise ValueError("session_id is required")
        client = self._client._client  # httpx.AsyncClient
        base = str(self._client._base_url).rstrip("/")
        url = f"{base}/sessions/{session_id}/events/stream"
        headers = {"Accept": "text/event-stream", **(self._client.auth_headers or {})}
        async with client.stream("GET", url, headers=headers, timeout=timeout) as resp:
            await _araise_for_stream_status(self, resp)
            event_name = ""
            data_buf: List[str] = []
            async for raw_line in resp.aiter_lines():
                line = raw_line
                if line == "":
                    if data_buf:
                        yield _decode_stream_frame(event_name, "\n".join(data_buf))
                    event_name = ""
                    data_buf = []
                    continue
                if line.startswith(":"):
                    continue
                name, _, value = line.partition(":")
                if value.startswith(" "):
                    value = value[1:]
                if name == "event":
                    event_name = value
                elif name == "data":
                    data_buf.append(value)
