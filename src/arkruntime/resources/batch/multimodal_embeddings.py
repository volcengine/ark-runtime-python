# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from typing import List, Optional

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
from ...types.multimodal_embedding.embedding_input_param import EmbeddingInputParam
from ...types.multimodal_embedding.encoding_format import EncodingFormat
from ...types.multimodal_embedding.multi_embedding_config_param import MultiEmbeddingConfigParam
from ...types.multimodal_embedding.multi_modal_embedding_request_param import MultiModalEmbeddingRequestParam
from ...types.multimodal_embedding.multi_modal_embedding_response import MultiModalEmbeddingResponse
from ...types.multimodal_embedding.sparse_embedding_config_param import SparseEmbeddingConfigParam

# AUTOGEN-END create-imports
from ._utils import async_with_batch_retry, get_request_last_time, with_batch_retry

__all__ = [
    "MultimodalEmbeddings",
    "AsyncMultimodalEmbeddings",
    "MultimodalEmbeddingsWithRawResponse",
    "AsyncMultimodalEmbeddingsWithRawResponse",
]


class MultimodalEmbeddings(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MultimodalEmbeddingsWithRawResponse:
        return MultimodalEmbeddingsWithRawResponse(self)

    @with_sts_token
    def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        input: List[EmbeddingInputParam],
        encoding_format: Optional[EncodingFormat] = None,
        dimensions: Optional[int] = None,
        sparse_embedding: Optional[SparseEmbeddingConfigParam] = None,
        multi_embedding: Optional[MultiEmbeddingConfigParam] = None,
        instructions: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> MultiModalEmbeddingResponse:
        deadline = get_request_last_time(self._client, timeout)
        breaker = self._client.get_model_breaker(model)

        return with_batch_retry(
            deadline,
            breaker,
            self._post_without_retry,
            "/batch/embeddings/multimodal",
            body=maybe_transform(
                {
                    # AUTOGEN-START create-body
                    "model": model,
                    "input": input,
                    "encoding_format": encoding_format,
                    "dimensions": dimensions,
                    "sparse_embedding": sparse_embedding,
                    "multi_embedding": multi_embedding,
                    "instructions": instructions,
                    # AUTOGEN-END create-body
                },
                MultiModalEmbeddingRequestParam,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=MultiModalEmbeddingResponse,
        )


class AsyncMultimodalEmbeddings(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMultimodalEmbeddingsWithRawResponse:
        return AsyncMultimodalEmbeddingsWithRawResponse(self)

    @async_with_sts_token
    async def create(
        self,
        *,
        # AUTOGEN-START create-kwargs
        model: str,
        input: List[EmbeddingInputParam],
        encoding_format: Optional[EncodingFormat] = None,
        dimensions: Optional[int] = None,
        sparse_embedding: Optional[SparseEmbeddingConfigParam] = None,
        multi_embedding: Optional[MultiEmbeddingConfigParam] = None,
        instructions: Optional[str] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> MultiModalEmbeddingResponse:
        deadline = get_request_last_time(self._client, timeout)
        breaker = await self._client.get_model_breaker(model)

        return await async_with_batch_retry(
            deadline,
            breaker,
            self._post_without_retry,
            "/batch/embeddings/multimodal",
            body=await async_maybe_transform(
                {
                    # AUTOGEN-START create-body
                    "model": model,
                    "input": input,
                    "encoding_format": encoding_format,
                    "dimensions": dimensions,
                    "sparse_embedding": sparse_embedding,
                    "multi_embedding": multi_embedding,
                    "instructions": instructions,
                    # AUTOGEN-END create-body
                },
                MultiModalEmbeddingRequestParam,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=MultiModalEmbeddingResponse,
        )


class MultimodalEmbeddingsWithRawResponse:
    def __init__(self, multimodal_embeddings: MultimodalEmbeddings) -> None:
        self._multimodal_embeddings = multimodal_embeddings
        self.create = to_raw_response_wrapper(multimodal_embeddings.create)


class AsyncMultimodalEmbeddingsWithRawResponse:
    def __init__(self, multimodal_embeddings: AsyncMultimodalEmbeddings) -> None:
        self._multimodal_embeddings = multimodal_embeddings
        self.create = async_to_raw_response_wrapper(multimodal_embeddings.create)
