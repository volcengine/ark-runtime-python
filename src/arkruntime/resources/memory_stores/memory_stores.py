from __future__ import annotations

from typing import List, Optional

from ..._base_client import make_request_options
from ..._compat import cached_property
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import NOT_GIVEN, NotGiven
from ...types.memory.delete_memory_store_response import DeleteMemoryStoreResponse
from ...types.memory.list_memory_stores_response import ListMemoryStoresResponse
from ...types.memory.memory_store import MemoryStore
from .memories import AsyncMemories, Memories

__all__ = ["MemoryStores", "AsyncMemoryStores"]

_PREFIX = "/memory_stores"


def _list_query(*, limit=NOT_GIVEN, page=NOT_GIVEN, created_by=NOT_GIVEN, name=NOT_GIVEN) -> dict:
    q: dict = {}
    for k, v in {"limit": limit, "page": page, "created_by": created_by, "name": name}.items():
        if v is not NOT_GIVEN and v is not None:
            q[k] = v
    return q


class MemoryStores(SyncAPIResource):
    @cached_property
    def memories(self) -> Memories:
        return Memories(self._client)

    def create(
        self,
        *,
        name: str,
        description=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> MemoryStore:
        return self._post(
            _PREFIX,
            body=dump_body({"name": name, "description": description, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryStore,
        )

    def retrieve(
        self, memory_store_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> MemoryStore:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return self._get(
            f"{_PREFIX}/{memory_store_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryStore,
        )

    def list(
        self,
        *,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        created_by: Optional[List[str]] | NotGiven = NOT_GIVEN,
        name=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListMemoryStoresResponse:
        return self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(limit=limit, page=page, created_by=created_by, name=name),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListMemoryStoresResponse,
        )

    def update(
        self,
        memory_store_id: str,
        *,
        name=NOT_GIVEN,
        description=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> MemoryStore:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return self._post(
            f"{_PREFIX}/{memory_store_id}",
            body=dump_body({"name": name, "description": description, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryStore,
        )

    def delete(
        self, memory_store_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteMemoryStoreResponse:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return self._delete(
            f"{_PREFIX}/{memory_store_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteMemoryStoreResponse,
        )


class AsyncMemoryStores(AsyncAPIResource):
    @cached_property
    def memories(self) -> AsyncMemories:
        return AsyncMemories(self._client)

    async def create(
        self,
        *,
        name: str,
        description=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> MemoryStore:
        return await self._post(
            _PREFIX,
            body=dump_body({"name": name, "description": description, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryStore,
        )

    async def retrieve(
        self, memory_store_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> MemoryStore:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return await self._get(
            f"{_PREFIX}/{memory_store_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryStore,
        )

    async def list(
        self,
        *,
        limit=NOT_GIVEN,
        page=NOT_GIVEN,
        created_by=NOT_GIVEN,
        name=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> ListMemoryStoresResponse:
        return await self._get(
            _PREFIX,
            options=make_request_options(
                query=_list_query(limit=limit, page=page, created_by=created_by, name=name),
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ListMemoryStoresResponse,
        )

    async def update(
        self,
        memory_store_id: str,
        *,
        name=NOT_GIVEN,
        description=NOT_GIVEN,
        metadata=NOT_GIVEN,
        extra_headers=None,
        extra_query=None,
        extra_body=None,
        timeout=None,
    ) -> MemoryStore:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return await self._post(
            f"{_PREFIX}/{memory_store_id}",
            body=dump_body({"name": name, "description": description, "metadata": metadata}),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MemoryStore,
        )

    async def delete(
        self, memory_store_id: str, *, extra_headers=None, extra_query=None, extra_body=None, timeout=None
    ) -> DeleteMemoryStoreResponse:
        if not memory_store_id:
            raise ValueError("memory_store_id is required")
        return await self._delete(
            f"{_PREFIX}/{memory_store_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DeleteMemoryStoreResponse,
        )
