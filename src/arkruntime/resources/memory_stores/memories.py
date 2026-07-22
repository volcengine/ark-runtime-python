from __future__ import annotations

from typing import Optional

from ..._base_client import make_request_options
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, NotGiven
from ...types.memory.delete_memory_response import DeleteMemoryResponse
from ...types.memory.list_memories_order_by import ListMemoriesOrderBy
from ...types.memory.list_memories_response import ListMemoriesResponse
from ...types.memory.memory import Memory

__all__ = ["Memories", "AsyncMemories"]


def _prefix(memory_store_id: str) -> str:
    return f"/memory_stores/{memory_store_id}/memories"


def _list_query(*, path_prefix=NOT_GIVEN, depth=NOT_GIVEN, order_by=NOT_GIVEN, limit=NOT_GIVEN, page=NOT_GIVEN) -> dict:
    q: dict = {}
    for k, v in {
        "path_prefix": path_prefix,
        "depth": depth,
        "order_by": order_by,
        "limit": limit,
        "page": page,
    }.items():
        if v is not NOT_GIVEN and v is not None:
            q[k] = v
    return q


class Memories(SyncAPIResource):
    def create(
        self,
        memory_store_id: str,
        *,
        path: str,
        content: str,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Memory:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return self._post(
            _prefix(memory_store_id),
            body=dump_body({"path": path, "content": content}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )

    def retrieve(
        self,
        memory_store_id: str,
        memory_id: str,
        *,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Memory:
        if not memory_store_id or not memory_id:
            raise ValueError("memory_store_id and memory_id are required")
        return self._get(
            f"{_prefix(memory_store_id)}/{memory_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )

    def list(
        self,
        memory_store_id: str,
        *,
        path_prefix=NOT_GIVEN,
        depth=NOT_GIVEN,
        order_by: Optional[ListMemoriesOrderBy] | NotGiven = NOT_GIVEN,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListMemoriesResponse:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return self._get(
            _prefix(memory_store_id),
            options=make_request_options(
                query=_list_query(path_prefix=path_prefix, depth=depth, order_by=order_by, limit=limit, page=page),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListMemoriesResponse,
        )

    def update(
        self,
        memory_store_id: str,
        memory_id: str,
        *,
        content=NOT_GIVEN,
        path=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Memory:
        if not memory_store_id or not memory_id:
            raise ValueError("memory_store_id and memory_id are required")
        return self._post(
            f"{_prefix(memory_store_id)}/{memory_id}",
            body=dump_body({"content": content, "path": path}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )

    def delete(
        self,
        memory_store_id: str,
        memory_id: str,
        *,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> DeleteMemoryResponse:
        if not memory_store_id or not memory_id:
            raise ValueError("memory_store_id and memory_id are required")
        return self._delete(
            f"{_prefix(memory_store_id)}/{memory_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteMemoryResponse,
        )


class AsyncMemories(AsyncAPIResource):
    async def create(
        self,
        memory_store_id: str,
        *,
        path: str,
        content: str,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Memory:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return await self._post(
            _prefix(memory_store_id),
            body=dump_body({"path": path, "content": content}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )

    async def retrieve(
        self,
        memory_store_id: str,
        memory_id: str,
        *,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Memory:
        if not memory_store_id or not memory_id:
            raise ValueError("memory_store_id and memory_id are required")
        return await self._get(
            f"{_prefix(memory_store_id)}/{memory_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )

    async def list(
        self,
        memory_store_id: str,
        *,
        path_prefix=NOT_GIVEN,
        depth=NOT_GIVEN,
        order_by=NOT_GIVEN,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListMemoriesResponse:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return await self._get(
            _prefix(memory_store_id),
            options=make_request_options(
                query=_list_query(path_prefix=path_prefix, depth=depth, order_by=order_by, limit=limit, page=page),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListMemoriesResponse,
        )

    async def update(
        self,
        memory_store_id: str,
        memory_id: str,
        *,
        content=NOT_GIVEN,
        path=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> Memory:
        if not memory_store_id or not memory_id:
            raise ValueError("memory_store_id and memory_id are required")
        return await self._post(
            f"{_prefix(memory_store_id)}/{memory_id}",
            body=dump_body({"content": content, "path": path}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Memory,
        )

    async def delete(
        self,
        memory_store_id: str,
        memory_id: str,
        *,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> DeleteMemoryResponse:
        if not memory_store_id or not memory_id:
            raise ValueError("memory_store_id and memory_id are required")
        return await self._delete(
            f"{_prefix(memory_store_id)}/{memory_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteMemoryResponse,
        )
