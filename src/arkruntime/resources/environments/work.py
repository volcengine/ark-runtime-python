# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

import httpx

from ..._base_client import make_request_options
from ..._managed_agents_serialize import dump_body
from ..._resource import AsyncAPIResource, SyncAPIResource
from ...types.environment.heartbeat_work_response import HeartbeatWorkResponse
from ...types.environment.stop_work_body import StopWorkBody
from ...types.environment.work_item import WorkItem

__all__ = ["EnvironmentWork", "AsyncEnvironmentWork"]

_WORKER_ID_HEADER = "Ark-Worker-ID"


def _path(environment_id: str, suffix: str) -> str:
    if not environment_id:
        raise ValueError("environment_id is required")
    return f"/environments/{quote(environment_id, safe='')}/work/{suffix.lstrip('/')}"


def _query(*, block_ms: int = 0, reclaim_older_than_ms: int = 0) -> dict:
    query = {}
    if block_ms > 0:
        query["block_ms"] = block_ms
    if reclaim_older_than_ms > 0:
        query["reclaim_older_than_ms"] = reclaim_older_than_ms
    return query


def _worker_headers(worker_id: str, extra_headers: Optional[dict]) -> dict:
    headers = dict(extra_headers or {})
    if worker_id:
        headers[_WORKER_ID_HEADER] = worker_id
    return headers


class EnvironmentWork(SyncAPIResource):
    def poll(
        self,
        environment_id: str,
        *,
        worker_id: str = "",
        block_ms: int = 999,
        reclaim_older_than_ms: int = 0,
        extra_headers=None,
        extra_query=None,
        timeout: float | httpx.Timeout | None = None,
    ) -> Optional[WorkItem]:
        raw = self._get(
            _path(environment_id, "poll"),
            options=make_request_options(
                query=_query(block_ms=block_ms, reclaim_older_than_ms=reclaim_older_than_ms),
                extra_headers=_worker_headers(worker_id, extra_headers),
                extra_query=extra_query,
                timeout=timeout,
            ),
            cast_to=object,
        )
        if not isinstance(raw, dict) or not raw.get("id"):
            return None
        try:
            return WorkItem.model_validate(raw)
        except Exception as exc:
            raise ValueError(f"invalid WorkItem response: {exc}") from exc

    def ack(
        self,
        environment_id: str,
        work_id: str,
        *,
        worker_id: str = "",
        extra_headers=None,
        timeout: float | httpx.Timeout | None = None,
    ) -> WorkItem:
        if not work_id:
            raise ValueError("work_id is required")
        return self._post_without_retry(
            _path(environment_id, f"{quote(work_id, safe='')}/ack"),
            options=make_request_options(
                extra_headers=_worker_headers(worker_id, extra_headers),
                timeout=timeout,
            ),
            cast_to=WorkItem,
        )

    def heartbeat(
        self,
        environment_id: str,
        work_id: str,
        *,
        expected_last_heartbeat: str = "",
        desired_ttl_seconds: int = 0,
        extra_headers=None,
        timeout: float | httpx.Timeout | None = None,
    ) -> HeartbeatWorkResponse:
        if not work_id:
            raise ValueError("work_id is required")
        query = {}
        if expected_last_heartbeat:
            query["expected_last_heartbeat"] = expected_last_heartbeat
        if desired_ttl_seconds > 0:
            query["desired_ttl_seconds"] = desired_ttl_seconds
        return self._post_without_retry(
            _path(environment_id, f"{quote(work_id, safe='')}/heartbeat"),
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                timeout=timeout,
            ),
            cast_to=HeartbeatWorkResponse,
        )

    def stop(
        self,
        environment_id: str,
        work_id: str,
        *,
        force: bool = False,
        extra_headers=None,
        timeout: float | httpx.Timeout | None = None,
    ) -> WorkItem:
        if not work_id:
            raise ValueError("work_id is required")
        body = StopWorkBody(force=True) if force else StopWorkBody()
        return self._post_without_retry(
            _path(environment_id, f"{quote(work_id, safe='')}/stop"),
            body=dump_body(body.model_dump(exclude_none=True, by_alias=True)),
            options=make_request_options(extra_headers=extra_headers, timeout=timeout),
            cast_to=WorkItem,
        )


class AsyncEnvironmentWork(AsyncAPIResource):
    async def poll(
        self,
        environment_id: str,
        *,
        worker_id: str = "",
        block_ms: int = 999,
        reclaim_older_than_ms: int = 0,
        extra_headers=None,
        extra_query=None,
        timeout: float | httpx.Timeout | None = None,
    ) -> Optional[WorkItem]:
        raw = await self._get(
            _path(environment_id, "poll"),
            options=make_request_options(
                query=_query(block_ms=block_ms, reclaim_older_than_ms=reclaim_older_than_ms),
                extra_headers=_worker_headers(worker_id, extra_headers),
                extra_query=extra_query,
                timeout=timeout,
            ),
            cast_to=object,
        )
        if not isinstance(raw, dict) or not raw.get("id"):
            return None
        try:
            return WorkItem.model_validate(raw)
        except Exception as exc:
            raise ValueError(f"invalid WorkItem response: {exc}") from exc

    async def ack(
        self,
        environment_id: str,
        work_id: str,
        *,
        worker_id: str = "",
        extra_headers=None,
        timeout: float | httpx.Timeout | None = None,
    ) -> WorkItem:
        if not work_id:
            raise ValueError("work_id is required")
        return await self._post_without_retry(
            _path(environment_id, f"{quote(work_id, safe='')}/ack"),
            options=make_request_options(
                extra_headers=_worker_headers(worker_id, extra_headers),
                timeout=timeout,
            ),
            cast_to=WorkItem,
        )

    async def heartbeat(
        self,
        environment_id: str,
        work_id: str,
        *,
        expected_last_heartbeat: str = "",
        desired_ttl_seconds: int = 0,
        extra_headers=None,
        timeout: float | httpx.Timeout | None = None,
    ) -> HeartbeatWorkResponse:
        if not work_id:
            raise ValueError("work_id is required")
        query = {}
        if expected_last_heartbeat:
            query["expected_last_heartbeat"] = expected_last_heartbeat
        if desired_ttl_seconds > 0:
            query["desired_ttl_seconds"] = desired_ttl_seconds
        return await self._post_without_retry(
            _path(environment_id, f"{quote(work_id, safe='')}/heartbeat"),
            options=make_request_options(
                query=query,
                extra_headers=extra_headers,
                timeout=timeout,
            ),
            cast_to=HeartbeatWorkResponse,
        )

    async def stop(
        self,
        environment_id: str,
        work_id: str,
        *,
        force: bool = False,
        extra_headers=None,
        timeout: float | httpx.Timeout | None = None,
    ) -> WorkItem:
        if not work_id:
            raise ValueError("work_id is required")
        body = StopWorkBody(force=True) if force else StopWorkBody()
        return await self._post_without_retry(
            _path(environment_id, f"{quote(work_id, safe='')}/stop"),
            body=dump_body(body.model_dump(exclude_none=True, by_alias=True)),
            options=make_request_options(extra_headers=extra_headers, timeout=timeout),
            cast_to=WorkItem,
        )
