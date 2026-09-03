# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from arkruntime.resources.files.files import AsyncFiles, Files


class _SyncClient:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def post(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.request = {"args": args, **kwargs}
        return {}

    def post_without_retry(self, *args: object, **kwargs: object) -> dict[str, object]:
        return self.post(*args, **kwargs)

    def get(self, *args: object, **kwargs: object) -> dict[str, object]:
        return {}

    def delete(self, *args: object, **kwargs: object) -> dict[str, object]:
        return {}

    def get_api_list(self, *args: object, **kwargs: object) -> list[object]:
        return []


class _AsyncClient:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    async def post(self, *args: object, **kwargs: object) -> dict[str, object]:
        self.request = {"args": args, **kwargs}
        return {}

    async def post_without_retry(self, *args: object, **kwargs: object) -> dict[str, object]:
        return await self.post(*args, **kwargs)

    async def get(self, *args: object, **kwargs: object) -> dict[str, object]:
        return {}

    async def delete(self, *args: object, **kwargs: object) -> dict[str, object]:
        return {}

    async def get_api_list(self, *args: object, **kwargs: object) -> list[object]:
        return []


def test_create_from_url_does_not_treat_url_as_local_file() -> None:
    client = _SyncClient()
    Files(client).create(purpose="user_data", url="https://example.com/file.pdf")

    assert client.request is not None
    assert client.request["files"] == []
    assert client.request["body"] == {
        "purpose": "user_data",
        "url": "https://example.com/file.pdf",
    }


@pytest.mark.asyncio
async def test_async_create_from_url_does_not_treat_url_as_local_file() -> None:
    client = _AsyncClient()
    await AsyncFiles(client).create(purpose="user_data", url="https://example.com/file.pdf")

    assert client.request is not None
    assert client.request["files"] == []
    assert client.request["body"] == {
        "purpose": "user_data",
        "url": "https://example.com/file.pdf",
    }


@pytest.mark.parametrize("kwargs", [{}, {"file": b"data", "url": "https://example.com/file.pdf"}])
def test_create_requires_exactly_one_file_source(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="Exactly one"):
        Files(_SyncClient()).create(purpose="user_data", **kwargs)
