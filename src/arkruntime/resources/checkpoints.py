from __future__ import annotations

from typing import List, Optional

from .._base_client import make_request_options
from .._managed_agents_serialize import dump_body
from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import NOT_GIVEN, NotGiven
from ..types.session.checkpoint_status import CheckpointStatus
from ..types.session.create_session_checkpoint_response import (
    CreateSessionCheckpointResponse,
)
from ..types.session.delete_session_checkpoint_response import (
    DeleteSessionCheckpointResponse,
)
from ..types.session.get_session_checkpoint_response import (
    GetSessionCheckpointResponse,
)
from ..types.session.list_session_checkpoints_response import (
    ListSessionCheckpointsResponse,
)

__all__ = ["Checkpoints", "AsyncCheckpoints"]

_PREFIX = "/checkpoints"


def _list_query(
    *,
    source_session_id=NOT_GIVEN,
    status=NOT_GIVEN,
    limit=NOT_GIVEN,
    page=NOT_GIVEN,
) -> dict:
    q: dict = {}
    for k, v in {
        "source_session_id": source_session_id,
        "status": status,
        "limit": limit,
        "page": page,
    }.items():
        if v is not NOT_GIVEN and v is not None:
            q[k] = v
    return q


class Checkpoints(SyncAPIResource):
    def create(
        self,
        session_id: str,
        *,
        name: str,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> CreateSessionCheckpointResponse:
        """Create a checkpoint of an idle Session.

        The returned checkpoint is initially ``creating`` and becomes
        ``ready`` once the asynchronous snapshot completes; only ready
        checkpoints can be used as ``checkpoint_id`` in
        ``sessions.create``.
        """
        if not session_id:
            raise ValueError("session_id is required")
        return self._post(
            f"/sessions/{session_id}/checkpoints",
            body=dump_body({"name": name}),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=CreateSessionCheckpointResponse,
        )

    def list(
        self,
        *,
        source_session_id: Optional[str] | NotGiven = NOT_GIVEN,
        status: Optional[List[CheckpointStatus]] | NotGiven = NOT_GIVEN,
        limit: Optional[int] | NotGiven = NOT_GIVEN,
        page: Optional[str] | NotGiven = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListSessionCheckpointsResponse:
        return self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(
                    source_session_id=source_session_id,
                    status=status,
                    limit=limit,
                    page=page,
                ),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListSessionCheckpointsResponse,
        )

    def retrieve(
        self,
        checkpoint_id: str,
        *,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> GetSessionCheckpointResponse:
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required")
        return self._get(
            f"{_PREFIX}/{checkpoint_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=GetSessionCheckpointResponse,
        )

    def delete(
        self,
        checkpoint_id: str,
        *,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> DeleteSessionCheckpointResponse:
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required")
        return self._delete(
            f"{_PREFIX}/{checkpoint_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=DeleteSessionCheckpointResponse,
        )


class AsyncCheckpoints(AsyncAPIResource):
    async def create(
        self,
        session_id: str,
        *,
        name: str,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> CreateSessionCheckpointResponse:
        """Async variant of :meth:`Checkpoints.create`."""
        if not session_id:
            raise ValueError("session_id is required")
        return await self._post(
            f"/sessions/{session_id}/checkpoints",
            body=dump_body({"name": name}),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=CreateSessionCheckpointResponse,
        )

    async def list(
        self,
        *,
        source_session_id: Optional[str] | NotGiven = NOT_GIVEN,
        status: Optional[List[CheckpointStatus]] | NotGiven = NOT_GIVEN,
        limit: Optional[int] | NotGiven = NOT_GIVEN,
        page: Optional[str] | NotGiven = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListSessionCheckpointsResponse:
        return await self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(
                    source_session_id=source_session_id,
                    status=status,
                    limit=limit,
                    page=page,
                ),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListSessionCheckpointsResponse,
        )

    async def retrieve(
        self,
        checkpoint_id: str,
        *,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> GetSessionCheckpointResponse:
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required")
        return await self._get(
            f"{_PREFIX}/{checkpoint_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=GetSessionCheckpointResponse,
        )

    async def delete(
        self,
        checkpoint_id: str,
        *,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> DeleteSessionCheckpointResponse:
        if not checkpoint_id:
            raise ValueError("checkpoint_id is required")
        return await self._delete(
            f"{_PREFIX}/{checkpoint_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=DeleteSessionCheckpointResponse,
        )
