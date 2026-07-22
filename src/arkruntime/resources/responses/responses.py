# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import (
    Iterable,
    List,
    Optional,
)
from urllib.parse import unquote_plus, urlparse

import httpx

from ..._base_client import make_request_options
from ..._compat import cached_property
from ..._exceptions import ArkAPIError
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._response import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ..._streaming import AsyncStream, Stream
from ..._types import Body, Headers, Query
from ..._utils import maybe_transform
from ..._utils._utils import async_with_sts_token, with_sts_token

# AUTOGEN-START create-imports
from ...types.responses.content_item_param import ContentItemParam as ResponseInputContentParam
from ...types.responses.context_management_param import ContextManagementParam
from ...types.responses.reasoning_param import ReasoningParam
from ...types.responses.response import Response
from ...types.responses.response_caching_param import ResponseCachingParam
from ...types.responses.response_includable import ResponseIncludable
from ...types.responses.response_stream_event import ResponseStreamEvent
from ...types.responses.response_text_config_param import ResponseTextConfigParam
from ...types.responses.responses_input_param import ResponsesInputParam
from ...types.responses.service_tier import ServiceTier
from ...types.responses.session_param import SessionParam
from ...types.responses.thinking_param import ThinkingParam
from ...types.responses.tool_choice_param import ToolChoiceParam
from ...types.responses.tool_param import ToolParam

# AUTOGEN-END create-imports

__all__ = ["Responses", "AsyncResponses"]

RESPONSES_MULTIMODAL_CONTENT_DATA_KEYS = {
    "input_image": "image_url",
    "input_video": "video_url",
    "input_file": "file_url",
}

FILE_PATH_SCHEME = "file"


def _add_beta_headers(extra_headers: Headers | None = None, tools: Iterable[ToolParam] | None = ()) -> Headers:
    if tools is None:
        return extra_headers
    for tool_param in tools:
        if tool_param.get("type", "") == "web_search":
            if extra_headers is None:
                extra_headers = {}
            extra_headers["ark-beta-web-search"] = "true"
        if tool_param.get("type", "") == "mcp":
            if extra_headers is None:
                extra_headers = {}
            extra_headers["ark-beta-mcp"] = "true"
        if tool_param.get("type", "") == "knowledge_search":
            if extra_headers is None:
                extra_headers = {}
            extra_headers["ark-beta-knowledge-search"] = "true"
        if tool_param.get("type", "") == "doubao_app":
            if extra_headers is None:
                extra_headers = {}
            extra_headers["ark-beta-doubao-app"] = "true"
        if tool_param.get("type", "") == "image_process":
            if extra_headers is None:
                extra_headers = {}
            extra_headers["ark-beta-image-process"] = "true"
    return extra_headers


class Responses(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ResponsesWithRawResponse:
        return ResponsesWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ResponsesWithStreamingResponse:
        return ResponsesWithStreamingResponse(self)

    @with_sts_token
    def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        input: ResponsesInputParam,
        model: str,
        max_output_tokens: Optional[int] = None,
        previous_response_id: Optional[str] = None,
        thinking: Optional[ThinkingParam] = None,
        service_tier: Optional[ServiceTier] = None,
        store: Optional[bool] = None,
        stream: Optional[bool] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolParam]] = None,
        top_p: Optional[float] = None,
        instructions: Optional[str] = None,
        include: Optional[List[ResponseIncludable]] = None,
        caching: Optional[ResponseCachingParam] = None,
        text: Optional[ResponseTextConfigParam] = None,
        expire_at: Optional[int] = None,
        tool_choice: Optional[ToolChoiceParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        max_tool_calls: Optional[int] = None,
        reasoning: Optional[ReasoningParam] = None,
        context_management: Optional[ContextManagementParam] = None,
        session: Optional[SessionParam] = None,
        prompt_cache_key: Optional[str] = None,
        safety_identifier: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | None = None,
    ) -> Response | Stream[ResponseStreamEvent]:
        extra_headers = _add_beta_headers(extra_headers, tools)
        resp = self._post(
            "/responses",
            body={
                # AUTOGEN-START create-body
                "input": input,
                "model": model,
                "max_output_tokens": max_output_tokens,
                "previous_response_id": previous_response_id,
                "thinking": thinking,
                "service_tier": service_tier,
                "store": store,
                "stream": stream,
                "temperature": temperature,
                "tools": tools,
                "top_p": top_p,
                "instructions": instructions,
                "include": include,
                "caching": caching,
                "text": text,
                "expire_at": expire_at,
                "tool_choice": tool_choice,
                "parallel_tool_calls": parallel_tool_calls,
                "max_tool_calls": max_tool_calls,
                "reasoning": reasoning,
                "context_management": context_management,
                "session": session,
                "prompt_cache_key": prompt_cache_key,
                "safety_identifier": safety_identifier,
                # AUTOGEN-END create-body
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=Response,
            stream=stream or False,
            stream_cls=Stream[ResponseStreamEvent],
        )
        return resp

    def retrieve(
        self,
        response_id: str,
        *,
        # AUTOGEN-START retrieve-kwargs
        include: Optional[List[ResponseIncludable]] = None,
        # AUTOGEN-END retrieve-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> Response:
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        return self._get(
            f"/responses/{response_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        # AUTOGEN-START retrieve-query
                        "include[]": include,
                        # AUTOGEN-END retrieve-query
                    },
                    dict,
                ),
            ),
            cast_to=Response,
            stream=False,
            stream_cls=Stream[ResponseStreamEvent],
        )

    def delete(
        self,
        response_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> None:
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/responses/{response_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=type(None),
        )


class AsyncResponses(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncResponsesWithRawResponse:
        return AsyncResponsesWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncResponsesWithStreamingResponse:
        return AsyncResponsesWithStreamingResponse(self)

    @async_with_sts_token
    async def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        input: ResponsesInputParam,
        model: str,
        max_output_tokens: Optional[int] = None,
        previous_response_id: Optional[str] = None,
        thinking: Optional[ThinkingParam] = None,
        service_tier: Optional[ServiceTier] = None,
        store: Optional[bool] = None,
        stream: Optional[bool] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[ToolParam]] = None,
        top_p: Optional[float] = None,
        instructions: Optional[str] = None,
        include: Optional[List[ResponseIncludable]] = None,
        caching: Optional[ResponseCachingParam] = None,
        text: Optional[ResponseTextConfigParam] = None,
        expire_at: Optional[int] = None,
        tool_choice: Optional[ToolChoiceParam] = None,
        parallel_tool_calls: Optional[bool] = None,
        max_tool_calls: Optional[int] = None,
        reasoning: Optional[ReasoningParam] = None,
        context_management: Optional[ContextManagementParam] = None,
        session: Optional[SessionParam] = None,
        prompt_cache_key: Optional[str] = None,
        safety_identifier: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | None = None,
    ) -> Response | AsyncStream[ResponseStreamEvent]:
        extra_headers = _add_beta_headers(extra_headers, tools)
        await self._prepare_responses_input(input=input)

        resp = await self._post(
            "/responses",
            body={
                # AUTOGEN-START create-body
                "input": input,
                "model": model,
                "max_output_tokens": max_output_tokens,
                "previous_response_id": previous_response_id,
                "thinking": thinking,
                "service_tier": service_tier,
                "store": store,
                "stream": stream,
                "temperature": temperature,
                "tools": tools,
                "top_p": top_p,
                "instructions": instructions,
                "include": include,
                "caching": caching,
                "text": text,
                "expire_at": expire_at,
                "tool_choice": tool_choice,
                "parallel_tool_calls": parallel_tool_calls,
                "max_tool_calls": max_tool_calls,
                "reasoning": reasoning,
                "context_management": context_management,
                "session": session,
                "prompt_cache_key": prompt_cache_key,
                "safety_identifier": safety_identifier,
                # AUTOGEN-END create-body
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=Response,
            stream=stream or False,
            stream_cls=AsyncStream[ResponseStreamEvent],
        )

        return resp

    async def retrieve(
        self,
        response_id: str,
        *,
        # AUTOGEN-START retrieve-kwargs
        include: Optional[List[ResponseIncludable]] = None,
        # AUTOGEN-END retrieve-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> Response:
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        return await self._get(
            f"/responses/{response_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        # AUTOGEN-START retrieve-query
                        "include[]": include,
                        # AUTOGEN-END retrieve-query
                    },
                    dict,
                ),
            ),
            cast_to=Response,
            stream=False,
            stream_cls=Stream[ResponseStreamEvent],
        )

    async def delete(
        self,
        response_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> None:
        if not response_id:
            raise ValueError(f"Expected a non-empty value for `response_id` but received {response_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/responses/{response_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=type(None),
        )

    async def _prepare_responses_input(self, input: ResponsesInputParam):
        tasks = []
        for input_item in input:  # type: ResponseInputItemParam
            if "content" not in input_item:  # skip non-content message
                continue
            content_list = input_item["content"]

            if not isinstance(content_list, list):  # skip non-list content
                continue

            for content in content_list:  # type: ResponseInputContentParam
                tasks.append(self._prepare_responses_input_file(content=content))

        await asyncio.gather(*tasks)

    async def _prepare_responses_input_file(self, content: ResponseInputContentParam):
        if "type" not in content:  # skip non-type content
            return
        content_type = content["type"]
        if content_type not in RESPONSES_MULTIMODAL_CONTENT_DATA_KEYS.keys():  # skip non-multimodal content
            return
        content_data_key = RESPONSES_MULTIMODAL_CONTENT_DATA_KEYS[content_type]
        if content_data_key not in content:  # skip non-url content
            return
        content_data: str = content[content_data_key]

        parsed = urlparse(content_data)
        if parsed.scheme != FILE_PATH_SCHEME:  # skip non-file-scheme content
            return

        # Decode percent-encoded parts in the path
        decoded_path = unquote_plus(parsed.path)

        if parsed.netloc:
            # Handle cases like file://hostname/share/path or Windows UNC
            # For simplicity, prefix double-slash for network path
            full_path = f"{parsed.netloc}{decoded_path}"
        else:
            full_path = decoded_path

        file_path = Path(full_path)
        file = await self._client.files.create(file=file_path, purpose="user_data")
        file = await self._client.files.wait_for_processing(id=file.id)
        if file.status != "active":
            raise ArkAPIError(f"File path: {full_path},id: {file.id} processing failed with status {file.status}.")

        # replace with file id
        content[content_data_key] = None
        content["file_id"] = file.id


class ResponsesWithRawResponse:
    def __init__(self, responses: Responses) -> None:
        self._responses = responses

        self.create = to_raw_response_wrapper(
            responses.create,
        )


class AsyncResponsesWithRawResponse:
    def __init__(self, responses: AsyncResponses) -> None:
        self._responses = responses

        self.create = async_to_raw_response_wrapper(
            responses.create,
        )


class ResponsesWithStreamingResponse:
    def __init__(self, responses: Responses) -> None:
        self._responses = responses

        self.create = to_streamed_response_wrapper(
            responses.create,
        )


class AsyncResponsesWithStreamingResponse:
    def __init__(self, responses: AsyncResponses) -> None:
        self._responses = responses

        self.create = async_to_streamed_response_wrapper(
            responses.create,
        )
