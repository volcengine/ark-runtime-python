# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from typing import Optional

import httpx

from ..._base_client import make_request_options
from ..._compat import cached_property
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._response import (
    async_to_raw_response_wrapper,
    to_raw_response_wrapper,
)
from ..._types import Body, Headers, Query
from ..._utils import async_maybe_transform, maybe_transform

# AUTOGEN-START create-imports
from ...types.tokenization.tokenization_input_param import TokenizationInputParam
from ...types.tokenization.tokenization_request_param import TokenizationRequestParam
from ...types.tokenization.tokenization_response import TokenizationResponse

# AUTOGEN-END create-imports

__all__ = [
    "Tokenization",
    "AsyncTokenization",
    "TokenizationWithRawResponse",
    "AsyncTokenizationWithRawResponse",
]


class Tokenization(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TokenizationWithRawResponse:
        return TokenizationWithRawResponse(self)

    def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        text: TokenizationInputParam,
        user: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> TokenizationResponse:
        return self._post(
            "/tokenization",
            body=maybe_transform(
                {
                    # AUTOGEN-START create-body
                    "model": model,
                    "text": text,
                    "user": user,
                    # AUTOGEN-END create-body
                },
                TokenizationRequestParam,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=TokenizationResponse,
        )


class AsyncTokenization(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTokenizationWithRawResponse:
        return AsyncTokenizationWithRawResponse(self)

    async def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        text: TokenizationInputParam,
        user: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> TokenizationResponse:
        return await self._post(
            "/tokenization",
            body=await async_maybe_transform(
                {
                    # AUTOGEN-START create-body
                    "model": model,
                    "text": text,
                    "user": user,
                    # AUTOGEN-END create-body
                },
                TokenizationRequestParam,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=TokenizationResponse,
        )


class TokenizationWithRawResponse:
    def __init__(self, tokenization: Tokenization) -> None:
        self._tokenization = tokenization

        self.create = to_raw_response_wrapper(
            tokenization.create,
        )


class AsyncTokenizationWithRawResponse:
    def __init__(self, tokenization: AsyncTokenization) -> None:
        self._tokenization = tokenization

        self.create = async_to_raw_response_wrapper(
            tokenization.create,
        )
