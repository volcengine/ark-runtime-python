# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from typing import List, Optional

import httpx
from typing_extensions import Literal

from ..._base_client import make_request_options
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._types import Body, Headers, Query
from ..._utils import maybe_transform

# AUTOGEN-START create-imports
from ...types.content_generation.content_generation_task import ContentGenerationTask
from ...types.content_generation.content_item_param import ContentItemParam
from ...types.content_generation.create_content_generation_task_response import CreateContentGenerationTaskResponse
from ...types.content_generation.list_content_generation_tasks_response import ListContentGenerationTasksResponse
from ...types.content_generation.reasoning_effort import ReasoningEffort
from ...types.content_generation.tool_param import ToolParam

# AUTOGEN-END create-imports

__all__ = ["Tasks", "AsyncTasks"]

_BASE = "/contents/generations/tasks"


class Tasks(SyncAPIResource):
    def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        content: List[ContentItemParam],
        callback_url: Optional[str] = None,
        return_last_frame: Optional[bool] = None,
        service_tier: Optional[str] = None,
        execution_expires_after: Optional[int] = None,
        generate_audio: Optional[bool] = None,
        camera_fixed: Optional[bool] = None,
        watermark: Optional[bool] = None,
        seed: Optional[int] = None,
        resolution: Optional[str] = None,
        ratio: Optional[str] = None,
        duration: Optional[int] = None,
        frames: Optional[int] = None,
        subdivision_level: Optional[str] = None,
        file_format: Optional[str] = None,
        draft: Optional[bool] = None,
        optimize_prompt: Optional[bool] = None,
        tools: Optional[List[ToolParam]] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        human_face_mode: Optional[str] = None,
        safety_identifier: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> CreateContentGenerationTaskResponse:
        return self._post(
            _BASE,
            body={
                # AUTOGEN-START create-body
                "model": model,
                "content": content,
                "callback_url": callback_url,
                "return_last_frame": return_last_frame,
                "service_tier": service_tier,
                "execution_expires_after": execution_expires_after,
                "generate_audio": generate_audio,
                "camera_fixed": camera_fixed,
                "watermark": watermark,
                "seed": seed,
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
                "frames": frames,
                "subdivision_level": subdivision_level,
                "file_format": file_format,
                "draft": draft,
                "optimize_prompt": optimize_prompt,
                "tools": tools,
                "reasoning_effort": reasoning_effort,
                "human_face_mode": human_face_mode,
                "safety_identifier": safety_identifier,
                # AUTOGEN-END create-body
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=CreateContentGenerationTaskResponse,
        )

    def get(
        self,
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ContentGenerationTask:
        return self._get(
            f"{_BASE}/{task_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ContentGenerationTask,
        )

    def list(
        self,
        *,
        # AUTOGEN-START list-kwargs
        page_num: Optional[int] = None,
        page_size: Optional[int] = None,
        status: Optional[Literal["queued", "running", "cancelled", "succeeded", "failed"]] = None,
        task_ids: Optional[List[str]] = None,
        model: Optional[str] = None,
        service_tier: Optional[str] = None,
        # AUTOGEN-END list-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ListContentGenerationTasksResponse:
        return self._get(
            _BASE,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        # AUTOGEN-START list-query
                        "page_num": page_num,
                        "page_size": page_size,
                        "filter.status": status,
                        "filter.task_ids": task_ids,
                        "filter.model": model,
                        "filter.service_tier": service_tier,
                        # AUTOGEN-END list-query
                    },
                    dict,
                ),
            ),
            cast_to=ListContentGenerationTasksResponse,
        )

    def delete(
        self,
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> None:
        self._delete(
            f"{_BASE}/{task_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=type(None),
        )


class AsyncTasks(AsyncAPIResource):
    async def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        content: List[ContentItemParam],
        callback_url: Optional[str] = None,
        return_last_frame: Optional[bool] = None,
        service_tier: Optional[str] = None,
        execution_expires_after: Optional[int] = None,
        generate_audio: Optional[bool] = None,
        camera_fixed: Optional[bool] = None,
        watermark: Optional[bool] = None,
        seed: Optional[int] = None,
        resolution: Optional[str] = None,
        ratio: Optional[str] = None,
        duration: Optional[int] = None,
        frames: Optional[int] = None,
        subdivision_level: Optional[str] = None,
        file_format: Optional[str] = None,
        draft: Optional[bool] = None,
        optimize_prompt: Optional[bool] = None,
        tools: Optional[List[ToolParam]] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        human_face_mode: Optional[str] = None,
        safety_identifier: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> CreateContentGenerationTaskResponse:
        return await self._post(
            _BASE,
            body={
                # AUTOGEN-START create-body
                "model": model,
                "content": content,
                "callback_url": callback_url,
                "return_last_frame": return_last_frame,
                "service_tier": service_tier,
                "execution_expires_after": execution_expires_after,
                "generate_audio": generate_audio,
                "camera_fixed": camera_fixed,
                "watermark": watermark,
                "seed": seed,
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
                "frames": frames,
                "subdivision_level": subdivision_level,
                "file_format": file_format,
                "draft": draft,
                "optimize_prompt": optimize_prompt,
                "tools": tools,
                "reasoning_effort": reasoning_effort,
                "human_face_mode": human_face_mode,
                "safety_identifier": safety_identifier,
                # AUTOGEN-END create-body
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=CreateContentGenerationTaskResponse,
        )

    async def get(
        self,
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ContentGenerationTask:
        return await self._get(
            f"{_BASE}/{task_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ContentGenerationTask,
        )

    async def list(
        self,
        *,
        # AUTOGEN-START list-kwargs
        page_num: Optional[int] = None,
        page_size: Optional[int] = None,
        status: Optional[Literal["queued", "running", "cancelled", "succeeded", "failed"]] = None,
        task_ids: Optional[List[str]] = None,
        model: Optional[str] = None,
        service_tier: Optional[str] = None,
        # AUTOGEN-END list-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ListContentGenerationTasksResponse:
        return await self._get(
            _BASE,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        # AUTOGEN-START list-query
                        "page_num": page_num,
                        "page_size": page_size,
                        "filter.status": status,
                        "filter.task_ids": task_ids,
                        "filter.model": model,
                        "filter.service_tier": service_tier,
                        # AUTOGEN-END list-query
                    },
                    dict,
                ),
            ),
            cast_to=ListContentGenerationTasksResponse,
        )

    async def delete(
        self,
        task_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> None:
        await self._delete(
            f"{_BASE}/{task_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=type(None),
        )
