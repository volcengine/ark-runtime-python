from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Union

from ..._base_client import make_request_options
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, NotGiven
from ...types.session.list_session_threads_response import ListSessionThreadsResponse
from ...types.session.session_stream_shim import (
    ListSessionEventsResponse,
    SessionStreamEvent,
)
from ...types.session.session_thread import SessionThread
from .session_events import (
    _araise_for_stream_status,
    _decode_stream_frame,
    _list_events_query,
    _raise_for_stream_status,
)

__all__ = ["SessionThreads", "AsyncSessionThreads"]


def _list_threads_query(
    *,
    limit: Union[int, NotGiven] = NOT_GIVEN,
    page: Union[str, NotGiven] = NOT_GIVEN,
) -> Dict[str, Any]:
    q: Dict[str, Any] = {}
    if not isinstance(limit, NotGiven):
        q["limit"] = limit
    if not isinstance(page, NotGiven):
        q["page"] = page
    return q


class SessionThreads(SyncAPIResource):
    """Thread endpoints under a session.

    The primary thread is materialized lazily on the first event — send at
    least one user.message + wait for session.status_idle before expecting
    ``list()`` to return a non-empty page.
    """

    def list(
        self,
        session_id: str,
        *,
        limit: Union[int, NotGiven] = NOT_GIVEN,
        page: Union[str, NotGiven] = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListSessionThreadsResponse:
        if not session_id:
            raise ValueError("session_id is required")
        merged_query: Dict[str, Any] = {**_list_threads_query(limit=limit, page=page), **(extra_query or {})}
        return self._get(
            f"/sessions/{session_id}/threads",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=merged_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListSessionThreadsResponse,
        )

    def retrieve(
        self, session_id: str, thread_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> SessionThread:
        if not session_id:
            raise ValueError("session_id is required")
        if not thread_id:
            raise ValueError("thread_id is required")
        return self._get(
            f"/sessions/{session_id}/threads/{thread_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionThread,
        )

    def list_events(
        self,
        session_id: str,
        thread_id: str,
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
        if not session_id:
            raise ValueError("session_id is required")
        if not thread_id:
            raise ValueError("thread_id is required")
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
            f"/sessions/{session_id}/threads/{thread_id}/events",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=merged_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListSessionEventsResponse,
        )

    def stream(
        self, session_id: str, thread_id: str, *, timeout: Union[float, None] = None
    ) -> Iterator[SessionStreamEvent]:
        """SSE stream scoped to one thread. Same shape as
        :meth:`SessionEvents.stream`: yields :class:`SessionStreamEvent`
        for each frame — ``event.type`` gives the wire event type,
        ``event.data`` the parsed JSON payload."""
        if not session_id:
            raise ValueError("session_id is required")
        if not thread_id:
            raise ValueError("thread_id is required")
        client = self._client._client
        base = str(self._client._base_url).rstrip("/")
        url = f"{base}/sessions/{session_id}/threads/{thread_id}/stream"
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


class AsyncSessionThreads(AsyncAPIResource):
    async def list(
        self,
        session_id: str,
        *,
        limit: Union[int, NotGiven] = NOT_GIVEN,
        page: Union[str, NotGiven] = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListSessionThreadsResponse:
        if not session_id:
            raise ValueError("session_id is required")
        merged_query: Dict[str, Any] = {**_list_threads_query(limit=limit, page=page), **(extra_query or {})}
        return await self._get(
            f"/sessions/{session_id}/threads",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=merged_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListSessionThreadsResponse,
        )

    async def retrieve(
        self, session_id: str, thread_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> SessionThread:
        if not session_id:
            raise ValueError("session_id is required")
        if not thread_id:
            raise ValueError("thread_id is required")
        return await self._get(
            f"/sessions/{session_id}/threads/{thread_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionThread,
        )

    async def list_events(
        self,
        session_id: str,
        thread_id: str,
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
        if not session_id:
            raise ValueError("session_id is required")
        if not thread_id:
            raise ValueError("thread_id is required")
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
            f"/sessions/{session_id}/threads/{thread_id}/events",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=merged_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListSessionEventsResponse,
        )

    async def stream(
        self, session_id: str, thread_id: str, *, timeout: Union[float, None] = None
    ) -> AsyncIterator[SessionStreamEvent]:
        """Async variant of :meth:`SessionThreads.stream`. Yields
        :class:`SessionStreamEvent` for each frame."""
        if not session_id:
            raise ValueError("session_id is required")
        if not thread_id:
            raise ValueError("thread_id is required")
        client = self._client._client
        base = str(self._client._base_url).rstrip("/")
        url = f"{base}/sessions/{session_id}/threads/{thread_id}/stream"
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
