# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

import time
from typing import Mapping, Optional, cast

import httpx
from typing_extensions import Literal

from ... import _legacy_response
from ..._base_client import AsyncPaginator, make_request_options
from ..._compat import cached_property
from ..._resource import AsyncAPIResource, SyncAPIResource
from ..._response import (
    async_to_streamed_response_wrapper,
    to_streamed_response_wrapper,
)
from ..._types import Body, FileTypes, Headers, Query
from ..._utils import (
    async_maybe_transform,
    deepcopy_minimal,
    extract_files,
    maybe_transform,
)
from ...pagination import AsyncCursorPage, SyncCursorPage

# AUTOGEN-START create-imports
from ...types.file.file_create_request_param import FileCreateRequestParam
from ...types.file.file_deleted import FileDeleted
from ...types.file.file_object import FileObject
from ...types.file.preprocess_configs_param import PreprocessConfigsParam
from ...types.file.purpose_param import PurposeParam
from ...types.file.tos_storage_param import TosStorageParam

# AUTOGEN-END create-imports


__all__ = ["Files", "AsyncFiles"]


_TERMINAL_STATES = {"active", "failed"}
_DEFAULT_POLL_INTERVAL = 3.0
_DEFAULT_MAX_WAIT_SECONDS = 10 * 60


class Files(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> "FilesWithRawResponse":
        return FilesWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> "FilesWithStreamingResponse":
        return FilesWithStreamingResponse(self)

    def create(
        self,
        *,
        file: FileTypes,
        # AUTOGEN-START create-kwargs
        purpose: PurposeParam,
        preprocess_configs: Optional[PreprocessConfigsParam] = None,
        expire_at: Optional[int] = None,
        url: Optional[str] = None,
        tos: Optional[TosStorageParam] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> FileObject:
        """Upload a file that can be used across various endpoints.

        Args:
          file: The File object (path / bytes / open file / (filename, bytes) tuple)
            to be uploaded. Mutually exclusive with `url`.
          purpose: Intended purpose. Currently only `user_data` is supported.
          expire_at: Unix timestamp (seconds) after which the file is purged.
            Defaults to 7 days from upload.
          preprocess_configs: Preprocessing configuration to apply at upload.
          url: Alternative file source — http/https or `tos://` scheme.
            Mutually exclusive with `file`.
          tos: User-owned TOS bucket destination.
        """
        body = deepcopy_minimal(
            {
                "file": file,
                # AUTOGEN-START create-body
                "purpose": purpose,
                "preprocess_configs": preprocess_configs,
                "expire_at": expire_at,
                "url": url,
                "tos": tos,
                # AUTOGEN-END create-body
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return self._post(
            "/files",
            body=maybe_transform(body, FileCreateRequestParam),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=FileObject,
        )

    def retrieve(
        self,
        file_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> FileObject:
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return self._get(
            f"/files/{file_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=FileObject,
        )

    def list(
        self,
        *,
        # AUTOGEN-START list-kwargs
        purpose: Optional[Literal["user_data"]] = None,
        after: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[Literal["asc", "desc"]] = None,
        # AUTOGEN-END list-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> SyncCursorPage[FileObject]:
        return self._get_api_list(
            "/files",
            page=SyncCursorPage[FileObject],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        # AUTOGEN-START list-query
                        "purpose": purpose,
                        "after": after,
                        "limit": limit,
                        "order": order,
                        # AUTOGEN-END list-query
                    },
                    dict,
                ),
            ),
            model=FileObject,
        )

    def delete(
        self,
        file_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> FileDeleted:
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return self._delete(
            f"/files/{file_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=FileDeleted,
        )

    def wait_for_processing(
        self,
        id: str,
        *,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        max_wait_seconds: float = _DEFAULT_MAX_WAIT_SECONDS,
    ) -> FileObject:
        """Poll `retrieve` until status is terminal (active|failed) or the
        deadline elapses."""
        start = time.time()
        file = self.retrieve(id)
        while file.status not in _TERMINAL_STATES:
            self._sleep(poll_interval)
            file = self.retrieve(id)
            if time.time() - start > max_wait_seconds:
                raise RuntimeError(
                    f"Giving up on waiting for file {id} to finish processing after {max_wait_seconds} seconds."
                )
        return file


class AsyncFiles(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> "AsyncFilesWithRawResponse":
        return AsyncFilesWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> "AsyncFilesWithStreamingResponse":
        return AsyncFilesWithStreamingResponse(self)

    async def create(
        self,
        *,
        file: FileTypes,
        # AUTOGEN-START create-kwargs
        purpose: PurposeParam,
        preprocess_configs: Optional[PreprocessConfigsParam] = None,
        expire_at: Optional[int] = None,
        url: Optional[str] = None,
        tos: Optional[TosStorageParam] = None,
        # AUTOGEN-END create-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> FileObject:
        body = deepcopy_minimal(
            {
                "file": file,
                # AUTOGEN-START create-body
                "purpose": purpose,
                "preprocess_configs": preprocess_configs,
                "expire_at": expire_at,
                "url": url,
                "tos": tos,
                # AUTOGEN-END create-body
            }
        )
        files = extract_files(cast(Mapping[str, object], body), paths=[["file"]])
        extra_headers = {"Content-Type": "multipart/form-data", **(extra_headers or {})}
        return await self._post(
            "/files",
            body=await async_maybe_transform(body, FileCreateRequestParam),
            files=files,
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=FileObject,
        )

    async def retrieve(
        self,
        file_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> FileObject:
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return await self._get(
            f"/files/{file_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=FileObject,
        )

    def list(
        self,
        *,
        # AUTOGEN-START list-kwargs
        purpose: Optional[Literal["user_data"]] = None,
        after: Optional[str] = None,
        limit: Optional[int] = None,
        order: Optional[Literal["asc", "desc"]] = None,
        # AUTOGEN-END list-kwargs
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> AsyncPaginator[FileObject, AsyncCursorPage[FileObject]]:
        return self._get_api_list(
            "/files",
            page=AsyncCursorPage[FileObject],
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        # AUTOGEN-START list-query
                        "purpose": purpose,
                        "after": after,
                        "limit": limit,
                        "order": order,
                        # AUTOGEN-END list-query
                    },
                    dict,
                ),
            ),
            model=FileObject,
        )

    async def delete(
        self,
        file_id: str,
        *,
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None = None,
    ) -> FileDeleted:
        if not file_id:
            raise ValueError(f"Expected a non-empty value for `file_id` but received {file_id!r}")
        return await self._delete(
            f"/files/{file_id}",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
            ),
            cast_to=FileDeleted,
        )

    async def wait_for_processing(
        self,
        id: str,
        *,
        poll_interval: float = _DEFAULT_POLL_INTERVAL,
        max_wait_seconds: float = _DEFAULT_MAX_WAIT_SECONDS,
    ) -> FileObject:
        start = time.time()
        file = await self.retrieve(id)
        while file.status not in _TERMINAL_STATES:
            await self._sleep(poll_interval)
            file = await self.retrieve(id)
            if time.time() - start > max_wait_seconds:
                raise RuntimeError(
                    f"Giving up on waiting for file {id} to finish processing after {max_wait_seconds} seconds."
                )
        return file


class FilesWithRawResponse:
    def __init__(self, files: Files) -> None:
        self._files = files
        self.create = _legacy_response.to_raw_response_wrapper(files.create)
        self.retrieve = _legacy_response.to_raw_response_wrapper(files.retrieve)
        self.list = _legacy_response.to_raw_response_wrapper(files.list)
        self.delete = _legacy_response.to_raw_response_wrapper(files.delete)


class AsyncFilesWithRawResponse:
    def __init__(self, files: AsyncFiles) -> None:
        self._files = files
        self.create = _legacy_response.async_to_raw_response_wrapper(files.create)
        self.retrieve = _legacy_response.async_to_raw_response_wrapper(files.retrieve)
        self.list = _legacy_response.async_to_raw_response_wrapper(files.list)
        self.delete = _legacy_response.async_to_raw_response_wrapper(files.delete)


class FilesWithStreamingResponse:
    def __init__(self, files: Files) -> None:
        self._files = files
        self.create = to_streamed_response_wrapper(files.create)
        self.retrieve = to_streamed_response_wrapper(files.retrieve)
        self.list = to_streamed_response_wrapper(files.list)
        self.delete = to_streamed_response_wrapper(files.delete)


class AsyncFilesWithStreamingResponse:
    def __init__(self, files: AsyncFiles) -> None:
        self._files = files
        self.create = async_to_streamed_response_wrapper(files.create)
        self.retrieve = async_to_streamed_response_wrapper(files.retrieve)
        self.list = async_to_streamed_response_wrapper(files.list)
        self.delete = async_to_streamed_response_wrapper(files.delete)
