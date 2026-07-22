# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

import time
from typing import TYPE_CHECKING

import anyio

if TYPE_CHECKING:
    from ._client import Ark, AsyncArk


class SyncAPIResource:
    _client: "Ark"

    def __init__(self, client: "Ark") -> None:
        self._client = client
        self._post = client.post
        self._get = client.get
        self._delete = client.delete
        self._post_without_retry = client.post_without_retry
        self._get_api_list = client.get_api_list

    def _sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class AsyncAPIResource:
    _client: "AsyncArk"

    def __init__(self, client: "AsyncArk") -> None:
        self._client = client
        self._post = client.post
        self._get = client.get
        self._delete = client.delete
        self._post_without_retry = client.post_without_retry
        self._get_api_list = client.get_api_list

    async def _sleep(self, seconds: float) -> None:
        await anyio.sleep(seconds)
