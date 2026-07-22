from __future__ import annotations

from typing import List, Optional

from ..._base_client import make_request_options
from ..._compat import cached_property
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, NotGiven
from ...types.session.agent_identifier import AgentIdentifier
from ...types.session.delete_session_response import DeleteSessionResponse
from ...types.session.list_sessions_order import ListSessionsOrder
from ...types.session.list_sessions_response import ListSessionsResponse
from ...types.session.session import Session
from ...types.session.session_resource import SessionResource
from ...types.session.session_status import SessionStatus
from ...types.session.tag import Tag
from .session_events import AsyncSessionEvents, SessionEvents
from .session_resources import AsyncSessionResources, SessionResources
from .session_threads import AsyncSessionThreads, SessionThreads

__all__ = ["Sessions", "AsyncSessions"]

_PREFIX = "/sessions"


def _list_query(
    *,
    agent_id=NOT_GIVEN,
    agent_version=NOT_GIVEN,
    created_at_gt=NOT_GIVEN,
    created_at_gte=NOT_GIVEN,
    created_at_lt=NOT_GIVEN,
    created_at_lte=NOT_GIVEN,
    limit=NOT_GIVEN,
    memory_store_id=NOT_GIVEN,
    order=NOT_GIVEN,
    page=NOT_GIVEN,
    status=NOT_GIVEN,
) -> dict:
    q: dict = {}
    for k, v in {
        "agent_id": agent_id,
        "agent_version": agent_version,
        "created_at_gt": created_at_gt,
        "created_at_gte": created_at_gte,
        "created_at_lt": created_at_lt,
        "created_at_lte": created_at_lte,
        "limit": limit,
        "memory_store_id": memory_store_id,
        "order": order,
        "page": page,
        "status": status,
    }.items():
        if v is not NOT_GIVEN and v is not None:
            q[k] = v
    return q


class Sessions(SyncAPIResource):
    @cached_property
    def resources(self) -> SessionResources:
        return SessionResources(self._client)

    @cached_property
    def events(self) -> SessionEvents:
        return SessionEvents(self._client)

    @cached_property
    def threads(self) -> SessionThreads:
        return SessionThreads(self._client)

    def create(
        self,
        *,
        agent: AgentIdentifier,
        environment_id: str,
        tags: Optional[List[Tag]] | NotGiven = NOT_GIVEN,
        resources: Optional[List[SessionResource]] | NotGiven = NOT_GIVEN,
        title: Optional[str] | NotGiven = NOT_GIVEN,
        vault_ids: Optional[List[str]] | NotGiven = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Session:
        return self._post(
            _PREFIX,
            body=dump_body(
                {
                    "agent": agent,
                    "environment_id": environment_id,
                    "tags": tags,
                    "resources": resources,
                    "title": title,
                    "vault_ids": vault_ids,
                }
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Session,
        )

    def retrieve(
        self, session_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Session:
        if not session_id:
            raise ValueError("session_id is required")
        return self._get(
            f"{_PREFIX}/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Session,
        )

    def list(
        self,
        *,
        agent_id=NOT_GIVEN,
        agent_version=NOT_GIVEN,
        created_at_gt=NOT_GIVEN,
        created_at_gte=NOT_GIVEN,
        created_at_lt=NOT_GIVEN,
        created_at_lte=NOT_GIVEN,
        limit=NOT_GIVEN,
        memory_store_id=NOT_GIVEN,
        order: Optional[ListSessionsOrder] | NotGiven = NOT_GIVEN,
        page=NOT_GIVEN,
        status: Optional[List[SessionStatus]] | NotGiven = NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListSessionsResponse:
        return self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(
                    agent_id=agent_id,
                    agent_version=agent_version,
                    created_at_gt=created_at_gt,
                    created_at_gte=created_at_gte,
                    created_at_lt=created_at_lt,
                    created_at_lte=created_at_lte,
                    limit=limit,
                    memory_store_id=memory_store_id,
                    order=order,
                    page=page,
                    status=status,
                ),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListSessionsResponse,
        )

    def update(
        self,
        session_id: str,
        *,
        tags=NOT_GIVEN,
        title=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Session:
        if not session_id:
            raise ValueError("session_id is required")
        return self._post(
            f"{_PREFIX}/{session_id}",
            body=dump_body({"tags": tags, "title": title}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Session,
        )

    def delete(
        self, session_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteSessionResponse:
        if not session_id:
            raise ValueError("session_id is required")
        return self._delete(
            f"{_PREFIX}/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteSessionResponse,
        )


class AsyncSessions(AsyncAPIResource):
    @cached_property
    def resources(self) -> AsyncSessionResources:
        return AsyncSessionResources(self._client)

    @cached_property
    def events(self) -> AsyncSessionEvents:
        return AsyncSessionEvents(self._client)

    @cached_property
    def threads(self) -> AsyncSessionThreads:
        return AsyncSessionThreads(self._client)

    async def create(
        self,
        *,
        agent: AgentIdentifier,
        environment_id: str,
        tags=NOT_GIVEN,
        resources=NOT_GIVEN,
        title=NOT_GIVEN,
        vault_ids=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Session:
        return await self._post(
            _PREFIX,
            body=dump_body(
                {
                    "agent": agent,
                    "environment_id": environment_id,
                    "tags": tags,
                    "resources": resources,
                    "title": title,
                    "vault_ids": vault_ids,
                }
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Session,
        )

    async def retrieve(
        self, session_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Session:
        if not session_id:
            raise ValueError("session_id is required")
        return await self._get(
            f"{_PREFIX}/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Session,
        )

    async def list(
        self,
        *,
        agent_id=NOT_GIVEN,
        agent_version=NOT_GIVEN,
        created_at_gt=NOT_GIVEN,
        created_at_gte=NOT_GIVEN,
        created_at_lt=NOT_GIVEN,
        created_at_lte=NOT_GIVEN,
        limit=NOT_GIVEN,
        memory_store_id=NOT_GIVEN,
        order=NOT_GIVEN,
        page=NOT_GIVEN,
        status=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListSessionsResponse:
        return await self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(
                    agent_id=agent_id,
                    agent_version=agent_version,
                    created_at_gt=created_at_gt,
                    created_at_gte=created_at_gte,
                    created_at_lt=created_at_lt,
                    created_at_lte=created_at_lte,
                    limit=limit,
                    memory_store_id=memory_store_id,
                    order=order,
                    page=page,
                    status=status,
                ),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListSessionsResponse,
        )

    async def update(
        self,
        session_id: str,
        *,
        tags=NOT_GIVEN,
        title=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Session:
        if not session_id:
            raise ValueError("session_id is required")
        return await self._post(
            f"{_PREFIX}/{session_id}",
            body=dump_body({"tags": tags, "title": title}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Session,
        )

    async def delete(
        self, session_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteSessionResponse:
        if not session_id:
            raise ValueError("session_id is required")
        return await self._delete(
            f"{_PREFIX}/{session_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteSessionResponse,
        )
