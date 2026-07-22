from __future__ import annotations

from ..._base_client import make_request_options
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ...types.session.list_session_resources_response import (
    ListSessionResourcesResponse,
)
from ...types.session.session_resource import SessionResource

__all__ = ["SessionResources", "AsyncSessionResources"]


def _prefix(session_id: str) -> str:
    return f"/sessions/{session_id}/resources"


class SessionResources(SyncAPIResource):
    def create(
        self,
        session_id: str,
        *,
        file_id: str,
        type: str = "file",
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> SessionResource:
        if not session_id:
            raise ValueError("session_id is required")
        return self._post(
            _prefix(session_id),
            body=dump_body({"file_id": file_id, "type": type}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionResource,
        )

    def list(
        self, session_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> ListSessionResourcesResponse:
        if not session_id:
            raise ValueError("session_id is required")
        return self._get(
            _prefix(session_id),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListSessionResourcesResponse,
        )


class AsyncSessionResources(AsyncAPIResource):
    async def create(
        self,
        session_id: str,
        *,
        file_id: str,
        type: str = "file",
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> SessionResource:
        if not session_id:
            raise ValueError("session_id is required")
        return await self._post(
            _prefix(session_id),
            body=dump_body({"file_id": file_id, "type": type}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SessionResource,
        )

    async def list(
        self, session_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> ListSessionResourcesResponse:
        if not session_id:
            raise ValueError("session_id is required")
        return await self._get(
            _prefix(session_id),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ListSessionResourcesResponse,
        )
