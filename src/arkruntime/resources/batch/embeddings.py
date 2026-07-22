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
from ..._utils._utils import async_with_sts_token, with_sts_token

# AUTOGEN-START create-imports
from ...types.embedding.embedding_input_param import EmbeddingInputParam
from ...types.embedding.embedding_request_param import EmbeddingRequestParam
from ...types.embedding.embedding_response import EmbeddingResponse
from ...types.embedding.encoding_format import EncodingFormat

# AUTOGEN-END create-imports
from ._utils import async_with_batch_retry, get_request_last_time, with_batch_retry

__all__ = [
    "Embeddings",
    "AsyncEmbeddings",
    "EmbeddingsWithRawResponse",
    "AsyncEmbeddingsWithRawResponse",
]


class Embeddings(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> EmbeddingsWithRawResponse:
        return EmbeddingsWithRawResponse(self)

    @with_sts_token
    def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        input: EmbeddingInputParam,
        encoding_format: Optional[EncodingFormat] = None,
        dimensions: Optional[int] = None,
        user: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> EmbeddingResponse:
        deadline = get_request_last_time(self._client, timeout)
        breaker = self._client.get_model_breaker(model)

        return with_batch_retry(
            deadline,
            breaker,
            self._post_without_retry,
            "/batch/embeddings",
            body=maybe_transform(
                {
                    # AUTOGEN-START create-body
                    "model": model,
                    "input": input,
                    "encoding_format": encoding_format,
                    "dimensions": dimensions,
                    "user": user,
                    # AUTOGEN-END create-body
                },
                EmbeddingRequestParam,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=EmbeddingResponse,
        )


class AsyncEmbeddings(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncEmbeddingsWithRawResponse:
        return AsyncEmbeddingsWithRawResponse(self)

    @async_with_sts_token
    async def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        input: EmbeddingInputParam,
        encoding_format: Optional[EncodingFormat] = None,
        dimensions: Optional[int] = None,
        user: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> EmbeddingResponse:
        deadline = get_request_last_time(self._client, timeout)
        breaker = await self._client.get_model_breaker(model)

        return await async_with_batch_retry(
            deadline,
            breaker,
            self._post_without_retry,
            "/batch/embeddings",
            body=await async_maybe_transform(
                {
                    # AUTOGEN-START create-body
                    "model": model,
                    "input": input,
                    "encoding_format": encoding_format,
                    "dimensions": dimensions,
                    "user": user,
                    # AUTOGEN-END create-body
                },
                EmbeddingRequestParam,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=EmbeddingResponse,
        )


class EmbeddingsWithRawResponse:
    def __init__(self, embeddings: Embeddings) -> None:
        self._embeddings = embeddings
        self.create = to_raw_response_wrapper(embeddings.create)


class AsyncEmbeddingsWithRawResponse:
    def __init__(self, embeddings: AsyncEmbeddings) -> None:
        self._embeddings = embeddings
        self.create = async_to_raw_response_wrapper(embeddings.create)
