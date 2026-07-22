# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from typing import List, Optional

import httpx

from ..._base_client import make_request_options
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._streaming import AsyncStream, Stream
from ..._types import Body, Headers, Query

# AUTOGEN-START create-imports
from ...types.images.image_generation_response import ImageGenerationResponse
from ...types.images.image_generation_stream_event import ImageGenerationStreamEvent
from ...types.images.optimize_prompt_options_param import OptimizePromptOptionsParam
from ...types.images.output_format import OutputFormat
from ...types.images.response_format import ResponseFormat
from ...types.images.sequential_image_generation_mode import SequentialImageGenerationMode
from ...types.images.sequential_image_generation_options_param import SequentialImageGenerationOptionsParam
from ...types.images.tool_param import ToolParam

# AUTOGEN-END create-imports

__all__ = ["Images", "AsyncImages"]

_PATH = "/images/generations"


class Images(SyncAPIResource):
    def generate(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        prompt: str,
        image: Optional[List[str]] = None,
        stream: Optional[bool] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        image_guidance_scale: Optional[float] = None,
        size: Optional[str] = None,
        watermark: Optional[bool] = None,
        sequential_image_generation: Optional[SequentialImageGenerationMode] = None,
        sequential_image_generation_options: Optional[SequentialImageGenerationOptionsParam] = None,
        optimize_prompt_options: Optional[OptimizePromptOptionsParam] = None,
        tools: Optional[List[ToolParam]] = None,
        output_format: Optional[OutputFormat] = None,
        layer_decomposition: Optional[bool] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ImageGenerationResponse | Stream[ImageGenerationStreamEvent]:
        return self._post(
            _PATH,
            body={
                # AUTOGEN-START create-body
                "model": model,
                "prompt": prompt,
                "image": image,
                "stream": stream,
                "response_format": response_format,
                "seed": seed,
                "guidance_scale": guidance_scale,
                "image_guidance_scale": image_guidance_scale,
                "size": size,
                "watermark": watermark,
                "sequential_image_generation": sequential_image_generation,
                "sequential_image_generation_options": sequential_image_generation_options,
                "optimize_prompt_options": optimize_prompt_options,
                "tools": tools,
                "output_format": output_format,
                "layer_decomposition": layer_decomposition,
                # AUTOGEN-END create-body
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ImageGenerationResponse,
            stream=stream or False,
            stream_cls=Stream[ImageGenerationStreamEvent],
        )


class AsyncImages(AsyncAPIResource):
    async def generate(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        prompt: str,
        image: Optional[List[str]] = None,
        stream: Optional[bool] = None,
        response_format: Optional[ResponseFormat] = None,
        seed: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        image_guidance_scale: Optional[float] = None,
        size: Optional[str] = None,
        watermark: Optional[bool] = None,
        sequential_image_generation: Optional[SequentialImageGenerationMode] = None,
        sequential_image_generation_options: Optional[SequentialImageGenerationOptionsParam] = None,
        optimize_prompt_options: Optional[OptimizePromptOptionsParam] = None,
        tools: Optional[List[ToolParam]] = None,
        output_format: Optional[OutputFormat] = None,
        layer_decomposition: Optional[bool] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ImageGenerationResponse | AsyncStream[ImageGenerationStreamEvent]:
        return await self._post(
            _PATH,
            body={
                # AUTOGEN-START create-body
                "model": model,
                "prompt": prompt,
                "image": image,
                "stream": stream,
                "response_format": response_format,
                "seed": seed,
                "guidance_scale": guidance_scale,
                "image_guidance_scale": image_guidance_scale,
                "size": size,
                "watermark": watermark,
                "sequential_image_generation": sequential_image_generation,
                "sequential_image_generation_options": sequential_image_generation_options,
                "optimize_prompt_options": optimize_prompt_options,
                "tools": tools,
                "output_format": output_format,
                "layer_decomposition": layer_decomposition,
                # AUTOGEN-END create-body
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ImageGenerationResponse,
            stream=stream or False,
            stream_cls=AsyncStream[ImageGenerationStreamEvent],
        )
