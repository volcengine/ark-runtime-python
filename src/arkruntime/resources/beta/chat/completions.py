# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from functools import partial
from typing import Dict, List, Optional, cast

import httpx

from ...._resource import AsyncAPIResource, SyncAPIResource
from ...._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from ....common._parsing import (
    ResponseFormatT,
    parse_chat_completion,
    type_to_response_format_param,
    validate_input_tools,
)
from ....common.streaming.chat import (
    AsyncChatCompletionStreamManager,
    ChatCompletionStreamManager,
)
from ....types.chat import ParsedChatCompletion
from ....types.chat.chat_completion_request_message_param import (
    ChatCompletionRequestMessageParam,
)
from ....types.chat.chat_completion_response_format_param import (
    ChatCompletionResponseFormatParam,
)
from ....types.chat.chat_completion_stop_param import ChatCompletionStopParam
from ....types.chat.chat_completion_stream_options_param import (
    ChatCompletionStreamOptionsParam,
)
from ....types.chat.chat_completion_tool_choice_param import (
    ChatCompletionToolChoiceParam,
)
from ....types.chat.chat_completion_tool_param import ChatCompletionToolParam
from ....types.chat.reasoning_effort import ReasoningEffort
from ....types.chat.request_service_tier import RequestServiceTier
from ....types.chat.thinking_param import ThinkingParam

__all__ = ["Completions", "AsyncCompletions"]


class Completions(SyncAPIResource):
    """Beta chat completions with auto-parsing of structured outputs.

    Mirrors the standard ``client.beta.chat.completions`` surface: ``parse``
    returns a :class:`ParsedChatCompletion` whose ``message.parsed`` is the
    deserialised Pydantic model (or ``message.tool_calls[i].function.parsed_arguments``
    for tool calls), and ``stream`` returns a context manager yielding typed
    events as the response is produced.
    """

    def parse(
        self,
        *,
        messages: List[ChatCompletionRequestMessageParam],
        model: str,
        response_format: type[ResponseFormatT] | NotGiven = NOT_GIVEN,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        n: Optional[int] = None,
        stop: Optional[ChatCompletionStopParam] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tool_choice: Optional[ChatCompletionToolChoiceParam] = None,
        tools: Optional[List[ChatCompletionToolParam]] = None,
        parallel_tool_calls: Optional[bool] = None,
        user: Optional[str] = None,
        service_tier: Optional[RequestServiceTier] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        thinking: Optional[ThinkingParam] = None,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ParsedChatCompletion[ResponseFormatT]:
        validate_input_tools(tools if tools is not None else NOT_GIVEN)

        raw_completion = self._client.chat.completions.create(
            messages=messages,
            model=model,
            response_format=cast(
                Optional[ChatCompletionResponseFormatParam],
                _resolve_response_format_param(response_format),
            ),
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
            n=n,
            stop=stop,
            temperature=temperature,
            top_p=top_p,
            tool_choice=tool_choice,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
            user=user,
            service_tier=service_tier,
            reasoning_effort=reasoning_effort,
            thinking=thinking,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=timeout,
        )

        return parse_chat_completion(
            response_format=response_format,
            input_tools=tools if tools is not None else NOT_GIVEN,
            chat_completion=raw_completion,
        )

    def stream(
        self,
        *,
        messages: List[ChatCompletionRequestMessageParam],
        model: str,
        response_format: type[ResponseFormatT] | ChatCompletionResponseFormatParam | NotGiven = NOT_GIVEN,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        n: Optional[int] = None,
        stop: Optional[ChatCompletionStopParam] = None,
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
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ChatCompletionStreamManager[ResponseFormatT]:
        api_request = partial(
            self._client.chat.completions.create,
            messages=messages,
            model=model,
            response_format=cast(
                Optional[ChatCompletionResponseFormatParam],
                _resolve_response_format_param(response_format),
            ),
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
            n=n,
            stop=stop,
            stream=True,
            stream_options=stream_options,
            temperature=temperature,
            top_p=top_p,
            tool_choice=tool_choice,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
            user=user,
            service_tier=service_tier,
            reasoning_effort=reasoning_effort,
            thinking=thinking,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=timeout,
        )

        return ChatCompletionStreamManager(
            cast("object", api_request),
            response_format=response_format,
            input_tools=tools if tools is not None else NOT_GIVEN,
        )


class AsyncCompletions(AsyncAPIResource):
    """Async variant of :class:`Completions`."""

    async def parse(
        self,
        *,
        messages: List[ChatCompletionRequestMessageParam],
        model: str,
        response_format: type[ResponseFormatT] | NotGiven = NOT_GIVEN,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        n: Optional[int] = None,
        stop: Optional[ChatCompletionStopParam] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tool_choice: Optional[ChatCompletionToolChoiceParam] = None,
        tools: Optional[List[ChatCompletionToolParam]] = None,
        parallel_tool_calls: Optional[bool] = None,
        user: Optional[str] = None,
        service_tier: Optional[RequestServiceTier] = None,
        reasoning_effort: Optional[ReasoningEffort] = None,
        thinking: Optional[ThinkingParam] = None,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> ParsedChatCompletion[ResponseFormatT]:
        validate_input_tools(tools if tools is not None else NOT_GIVEN)

        raw_completion = await self._client.chat.completions.create(
            messages=messages,
            model=model,
            response_format=cast(
                Optional[ChatCompletionResponseFormatParam],
                _resolve_response_format_param(response_format),
            ),
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
            n=n,
            stop=stop,
            temperature=temperature,
            top_p=top_p,
            tool_choice=tool_choice,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
            user=user,
            service_tier=service_tier,
            reasoning_effort=reasoning_effort,
            thinking=thinking,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=timeout,
        )

        return parse_chat_completion(
            response_format=response_format,
            input_tools=tools if tools is not None else NOT_GIVEN,
            chat_completion=raw_completion,
        )

    def stream(
        self,
        *,
        messages: List[ChatCompletionRequestMessageParam],
        model: str,
        response_format: type[ResponseFormatT] | ChatCompletionResponseFormatParam | NotGiven = NOT_GIVEN,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        logit_bias: Optional[Dict[str, float]] = None,
        logprobs: Optional[bool] = None,
        top_logprobs: Optional[int] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        n: Optional[int] = None,
        stop: Optional[ChatCompletionStopParam] = None,
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
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> AsyncChatCompletionStreamManager[ResponseFormatT]:
        api_request = self._client.chat.completions.create(
            messages=messages,
            model=model,
            response_format=cast(
                Optional[ChatCompletionResponseFormatParam],
                _resolve_response_format_param(response_format),
            ),
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            repetition_penalty=repetition_penalty,
            logit_bias=logit_bias,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            max_tokens=max_tokens,
            max_completion_tokens=max_completion_tokens,
            n=n,
            stop=stop,
            stream=True,
            stream_options=stream_options,
            temperature=temperature,
            top_p=top_p,
            tool_choice=tool_choice,
            tools=tools,
            parallel_tool_calls=parallel_tool_calls,
            user=user,
            service_tier=service_tier,
            reasoning_effort=reasoning_effort,
            thinking=thinking,
            extra_headers=extra_headers,
            extra_query=extra_query,
            extra_body=extra_body,
            timeout=timeout,
        )

        return AsyncChatCompletionStreamManager(
            cast("object", api_request),
            response_format=response_format,
            input_tools=tools if tools is not None else NOT_GIVEN,
        )


def _resolve_response_format_param(
    response_format: type[ResponseFormatT] | ChatCompletionResponseFormatParam | NotGiven,
) -> Optional[ChatCompletionResponseFormatParam]:
    """Translate a Pydantic class (or raw response_format dict) into the
    wire-format ``response_format`` parameter expected by chat.completions.

    Returns ``None`` when no response format was provided so the underlying
    ``create()`` skips the field entirely (matches the dict-style flow).
    """
    converted = type_to_response_format_param(response_format)
    if not isinstance(converted, dict):
        return None
    return cast(ChatCompletionResponseFormatParam, converted)
