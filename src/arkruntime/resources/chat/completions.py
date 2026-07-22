# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from typing import (
    Dict,
    List,
    Optional,
)

import httpx

from ..._base_client import make_request_options
from ..._compat import cached_property
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._response import (
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
)
from ..._streaming import AsyncStream, Stream
from ..._types import Body, Headers, Query
from ..._utils._utils import async_with_sts_token, with_sts_token

# AUTOGEN-START create-imports
from ...types.chat.chat_completion_request_message_param import ChatCompletionRequestMessageParam
from ...types.chat.chat_completion_response import ChatCompletionResponse
from ...types.chat.chat_completion_response_format_param import ChatCompletionResponseFormatParam
from ...types.chat.chat_completion_stop_param import ChatCompletionStopParam
from ...types.chat.chat_completion_stream_options_param import ChatCompletionStreamOptionsParam
from ...types.chat.chat_completion_stream_response import ChatCompletionStreamResponse
from ...types.chat.chat_completion_tool_choice_param import ChatCompletionToolChoiceParam
from ...types.chat.chat_completion_tool_param import ChatCompletionToolParam
from ...types.chat.reasoning_effort import ReasoningEffort
from ...types.chat.request_service_tier import RequestServiceTier
from ...types.chat.thinking_param import ThinkingParam
from ..encryption import async_with_e2e_encryption, with_e2e_encryption

# AUTOGEN-END create-imports

__all__ = ["Completions", "AsyncCompletions"]


class Completions(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CompletionsWithRawResponse:
        return CompletionsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CompletionsWithStreamingResponse:
        return CompletionsWithStreamingResponse(self)

    @with_sts_token
    @with_e2e_encryption
    def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        messages: List[ChatCompletionRequestMessageParam],
        model: str,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        n: Optional[int] = None,
        response_format: Optional[ChatCompletionResponseFormatParam] = None,
        stop: Optional[ChatCompletionStopParam] = None,
        stream: Optional[bool] = None,
        stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tool_choice: Optional[ChatCompletionToolChoiceParam] = None,
        tools: Optional[List[ChatCompletionToolParam]] = None,
        parallel_tool_calls: Optional[bool] = None,
        user: Optional[str] = None,
        service_tier: Optional[RequestServiceTier] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        thinking: Optional[ThinkingParam] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ChatCompletionResponse | Stream[ChatCompletionStreamResponse]:
        return self._post(
            "/chat/completions",
            body={
                # AUTOGEN-START create-body
                "messages": messages,
                "model": model,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "repetition_penalty": repetition_penalty,
                "logit_bias": logit_bias,
                "logprobs": logprobs,
                "top_logprobs": top_logprobs,
                "max_tokens": max_tokens,
                "max_completion_tokens": max_completion_tokens,
                "n": n,
                "response_format": response_format,
                "stop": stop,
                "stream": stream,
                "stream_options": stream_options,
                "temperature": temperature,
                "top_p": top_p,
                "tool_choice": tool_choice,
                "tools": tools,
                "parallel_tool_calls": parallel_tool_calls,
                "user": user,
                "service_tier": service_tier,
                "reasoning_effort": reasoning_effort,
                "thinking": thinking,
                # AUTOGEN-END create-body
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ChatCompletionResponse,
            stream=stream or False,
            stream_cls=Stream[ChatCompletionStreamResponse],
        )


class AsyncCompletions(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCompletionsWithRawResponse:
        return AsyncCompletionsWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCompletionsWithStreamingResponse:
        return AsyncCompletionsWithStreamingResponse(self)

    @async_with_sts_token
    @async_with_e2e_encryption
    async def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        messages: List[ChatCompletionRequestMessageParam],
        model: str,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        n: Optional[int] = None,
        response_format: Optional[ChatCompletionResponseFormatParam] = None,
        stop: Optional[ChatCompletionStopParam] = None,
        stream: Optional[bool] = None,
        stream_options: Optional[ChatCompletionStreamOptionsParam] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tool_choice: Optional[ChatCompletionToolChoiceParam] = None,
        tools: Optional[List[ChatCompletionToolParam]] = None,
        parallel_tool_calls: Optional[bool] = None,
        user: Optional[str] = None,
        service_tier: Optional[RequestServiceTier] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        thinking: Optional[ThinkingParam] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ChatCompletionResponse | AsyncStream[ChatCompletionStreamResponse]:
        return await self._post(
            "/chat/completions",
            body={
                # AUTOGEN-START create-body
                "messages": messages,
                "model": model,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "repetition_penalty": repetition_penalty,
                "logit_bias": logit_bias,
                "logprobs": logprobs,
                "top_logprobs": top_logprobs,
                "max_tokens": max_tokens,
                "max_completion_tokens": max_completion_tokens,
                "n": n,
                "response_format": response_format,
                "stop": stop,
                "stream": stream,
                "stream_options": stream_options,
                "temperature": temperature,
                "top_p": top_p,
                "tool_choice": tool_choice,
                "tools": tools,
                "parallel_tool_calls": parallel_tool_calls,
                "user": user,
                "service_tier": service_tier,
                "reasoning_effort": reasoning_effort,
                "thinking": thinking,
                # AUTOGEN-END create-body
            },
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=ChatCompletionResponse,
            stream=stream or False,
            stream_cls=AsyncStream[ChatCompletionStreamResponse],
        )


class CompletionsWithRawResponse:
    def __init__(self, completions: Completions) -> None:
        self._completions = completions
        self.create = to_raw_response_wrapper(completions.create)


class AsyncCompletionsWithRawResponse:
    def __init__(self, completions: AsyncCompletions) -> None:
        self._completions = completions
        self.create = async_to_raw_response_wrapper(completions.create)


class CompletionsWithStreamingResponse:
    def __init__(self, completions: Completions) -> None:
        self._completions = completions
        self.create = to_streamed_response_wrapper(completions.create)


class AsyncCompletionsWithStreamingResponse:
    def __init__(self, completions: AsyncCompletions) -> None:
        self._completions = completions
        self.create = async_to_streamed_response_wrapper(completions.create)
