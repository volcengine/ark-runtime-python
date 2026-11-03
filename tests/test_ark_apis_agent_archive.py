# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import secrets

import httpx
import pytest

from arkruntime import Ark, AsyncArk


@pytest.mark.parametrize("include", [None, False, True])
def test_agent_archive_transport(include):
    requests = []

    def respond(request):
        requests.append(request)
        data = (
            {
                "id": "resource/1",
                "type": "agent",
                "archived_at": "2026-10-29T00:00:00Z",
                "created_at": "2026-10-29T00:00:00Z",
                "updated_at": "2026-10-29T00:00:00Z",
                "name": "archive test",
                "version": 1,
            }
            if request.method == "POST"
            else {"data": [], "total": 0}
        )
        return httpx.Response(200, json=data)

    with Ark(
        api_key=secrets.token_hex(16),
        base_url="https://example.test/api/v3",
        http_client=httpx.Client(transport=httpx.MockTransport(respond)),
    ) as client:
        resource = client.agents
        result = resource.archive("resource/1")
        assert result.id == "resource/1"
        assert result.archived_at == "2026-10-29T00:00:00Z"
        request = requests[-1]
        assert request.method == "POST"
        assert request.url.raw_path == b"/api/v3/agents/resource%2F1/archive"
        assert request.content == b""
        if include is None:
            resource.list()
        else:
            resource.list(include_archived=include)
        request = requests[-1]
        assert request.method == "GET"
        assert request.url.params.get("include_archived") == (None if include is None else str(include).lower())
        with pytest.raises(ValueError, match="agent_id"):
            resource.archive("")


@pytest.mark.parametrize("include", [None, False, True])
def test_async_agent_archive_transport(include):
    async def run():
        requests = []

        def respond(request):
            requests.append(request)
            data = (
                {
                    "id": "resource/1",
                    "type": "agent",
                    "archived_at": "2026-10-29T00:00:00Z",
                    "created_at": "2026-10-29T00:00:00Z",
                    "updated_at": "2026-10-29T00:00:00Z",
                    "name": "archive test",
                    "version": 1,
                }
                if request.method == "POST"
                else {"data": [], "total": 0}
            )
            return httpx.Response(200, json=data)

        async with AsyncArk(
            api_key=secrets.token_hex(16),
            base_url="https://example.test/api/v3",
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)),
        ) as client:
            resource = client.agents
            result = await resource.archive("resource/1")
            assert result.id == "resource/1"
            assert result.archived_at == "2026-10-29T00:00:00Z"
            assert requests[-1].method == "POST"
            assert requests[-1].url.raw_path == b"/api/v3/agents/resource%2F1/archive"
            assert requests[-1].content == b""
            if include is None:
                await resource.list()
            else:
                await resource.list(include_archived=include)
            assert requests[-1].method == "GET"
            assert requests[-1].url.params.get("include_archived") == (
                None if include is None else str(include).lower()
            )
            with pytest.raises(ValueError, match="agent_id"):
                await resource.archive("")

    asyncio.run(run())
