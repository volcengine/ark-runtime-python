from __future__ import annotations

from typing import Optional

import httpx

from ..._base_client import make_request_options
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from ...types.environment.delete_environment_response import DeleteEnvironmentResponse
from ...types.environment.env_config import EnvConfig
from ...types.environment.environment import Environment
from ...types.environment.environment_scope import EnvironmentScope
from ...types.environment.list_environments_response import ListEnvironmentsResponse

__all__ = ["Environments", "AsyncEnvironments"]

_ENV_PREFIX = "/environments"


def _list_query(*, limit=NOT_GIVEN, page=NOT_GIVEN) -> dict:
    q: dict = {}
    if limit is not NOT_GIVEN and limit is not None:
        q["limit"] = limit
    if page is not NOT_GIVEN and page is not None:
        q["page"] = page
    return q


class Environments(SyncAPIResource):
    def create(
        self,
        *,
        name: str,
        config: Optional[EnvConfig] | NotGiven = NOT_GIVEN,
        description: Optional[str] | NotGiven = NOT_GIVEN,
        metadata: Optional[dict] | NotGiven = NOT_GIVEN,
        scope: Optional[EnvironmentScope] | NotGiven = NOT_GIVEN,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> Environment:
        return self._post(
            _ENV_PREFIX,
            body=dump_body(
                {"name": name, "config": config, "description": description, "metadata": metadata, "scope": scope}
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Environment,
        )

    def retrieve(
        self, environment_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Environment:
        if not environment_id:
            raise ValueError("environment_id is required")
        return self._get(
            f"{_ENV_PREFIX}/{environment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Environment,
        )

    def list(
        self, *, limit=NOT_GIVEN, page=NOT_GIVEN, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> ListEnvironmentsResponse:
        return self._get(
            _ENV_PREFIX,
            options=make_request_options(
                query=_list_query(limit=limit, page=page),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListEnvironmentsResponse,
        )

    def update(
        self,
        environment_id: str,
        *,
        name=NOT_GIVEN,
        config=NOT_GIVEN,
        description=NOT_GIVEN,
        metadata=NOT_GIVEN,
        scope=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Environment:
        if not environment_id:
            raise ValueError("environment_id is required")
        return self._post(
            f"{_ENV_PREFIX}/{environment_id}",
            body=dump_body(
                {"name": name, "config": config, "description": description, "metadata": metadata, "scope": scope}
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Environment,
        )

    def delete(
        self, environment_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteEnvironmentResponse:
        if not environment_id:
            raise ValueError("environment_id is required")
        return self._delete(
            f"{_ENV_PREFIX}/{environment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteEnvironmentResponse,
        )


class AsyncEnvironments(AsyncAPIResource):
    async def create(
        self,
        *,
        name: str,
        config=NOT_GIVEN,
        description=NOT_GIVEN,
        metadata=NOT_GIVEN,
        scope=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Environment:
        return await self._post(
            _ENV_PREFIX,
            body=dump_body(
                {"name": name, "config": config, "description": description, "metadata": metadata, "scope": scope}
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Environment,
        )

    async def retrieve(
        self, environment_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> Environment:
        if not environment_id:
            raise ValueError("environment_id is required")
        return await self._get(
            f"{_ENV_PREFIX}/{environment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Environment,
        )

    async def list(
        self, *, limit=NOT_GIVEN, page=NOT_GIVEN, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> ListEnvironmentsResponse:
        return await self._get(
            _ENV_PREFIX,
            options=make_request_options(
                query=_list_query(limit=limit, page=page),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListEnvironmentsResponse,
        )

    async def update(
        self,
        environment_id: str,
        *,
        name=NOT_GIVEN,
        config=NOT_GIVEN,
        description=NOT_GIVEN,
        metadata=NOT_GIVEN,
        scope=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Environment:
        if not environment_id:
            raise ValueError("environment_id is required")
        return await self._post(
            f"{_ENV_PREFIX}/{environment_id}",
            body=dump_body(
                {"name": name, "config": config, "description": description, "metadata": metadata, "scope": scope}
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Environment,
        )

    async def delete(
        self, environment_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteEnvironmentResponse:
        if not environment_id:
            raise ValueError("environment_id is required")
        return await self._delete(
            f"{_ENV_PREFIX}/{environment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteEnvironmentResponse,
        )
