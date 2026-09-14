# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from arkruntime.resources.skills.skills import AsyncSkills, Skills


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


def test_create_version_builds_multipart_request() -> None:
    client = _SyncClient()
    Skills(client).create_version(
        "skill-1",
        files=("skill.zip", b"zip-bytes"),
        display_title="Readiness Skill v2",
    )

    assert client.request is not None
    assert client.request["args"] == ("/skills/skill-1/versions",)
    assert client.request["body"] == {"display_title": "Readiness Skill v2"}
    assert client.request["files"] == {"files": ("skill.zip", b"zip-bytes")}


@pytest.mark.asyncio
async def test_async_create_version_builds_multipart_request() -> None:
    client = _AsyncClient()
    await AsyncSkills(client).create_version(
        "skill-1",
        files=("skill.zip", b"zip-bytes"),
        display_title="Readiness Skill v2",
    )

    assert client.request is not None
    assert client.request["args"] == ("/skills/skill-1/versions",)
    assert client.request["body"] == {"display_title": "Readiness Skill v2"}
    assert client.request["files"] == {"files": ("skill.zip", b"zip-bytes")}
