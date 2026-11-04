# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import asyncio

import httpx
import pytest

from arkruntime import Ark, AsyncArk
from arkruntime._list_response import normalize_list_response


@pytest.fixture(autouse=True)
def synthetic_credentials(monkeypatch):
    # MockTransport handles every request; no real credential is needed.
    monkeypatch.setenv("ARK_API_KEY", "placeholder")


@pytest.mark.parametrize("api", ["files", "resources"])
@pytest.mark.parametrize("payload", ["null", " \n null \t", '{"data":null}', '{"data":[]}'])
def test_null_lists_sync(api, payload):
    transport = httpx.MockTransport(
        lambda r: httpx.Response(200, text=payload, headers={"content-type": "application/json"})
    )
    with Ark(base_url="https://example.test/custom/v3", http_client=httpx.Client(transport=transport)) as client:
        result = client.files.list() if api == "files" else client.sessions.resources.list("session-1")
        assert result is not None
        assert result.data == []
        if api == "files":
            assert list(result) == []
            assert not result.has_next_page()


@pytest.mark.parametrize("api", ["files", "resources"])
@pytest.mark.parametrize("payload", ["null", " \n null \t", '{"data":null}', '{"data":[]}'])
def test_null_lists_async(api, payload):
    async def run():
        transport = httpx.MockTransport(
            lambda r: httpx.Response(200, text=payload, headers={"content-type": "application/json"})
        )
        http_client = httpx.AsyncClient(transport=transport)
        async with AsyncArk(base_url="https://example.test/custom/v3", http_client=http_client) as client:
            result = await client.files.list() if api == "files" else await client.sessions.resources.list("session-1")
            assert result is not None
            assert result.data == []
            if api == "files":
                assert [item async for item in result] == []
                assert not result.has_next_page()

    asyncio.run(run())


def test_pagination_and_nonempty_items_are_preserved():
    payload = {
        "object": "file",
        "data": [{"id": "file-1"}],
        "first_id": "file-1",
        "last_id": "file-1",
        "has_more": True,
    }
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    with Ark(http_client=httpx.Client(transport=transport)) as client:
        result = client.files.list()
        assert result.data[0].id == "file-1"
        assert result.first_id == result.last_id == "file-1"
        assert result.has_next_page()


@pytest.mark.parametrize(
    "path,method,status",
    [
        ("/files/file-1", "GET", 200),
        ("/agents", "GET", 200),
        ("/files", "POST", 200),
        ("/files", "GET", 400),
        ("/sessions/session-1/resources", "POST", 200),
    ],
)
def test_other_operations_and_errors_are_not_normalized(path, method, status):
    response = httpx.Response(status, request=httpx.Request(method, "https://example.test" + path))
    assert normalize_list_response(None, response, "") is None


@pytest.mark.parametrize("data", [{}, {"data": "invalid"}, [], "invalid", 123])
def test_invalid_shapes_are_not_normalized(data):
    response = httpx.Response(200, request=httpx.Request("GET", "https://example.test/files"))
    assert normalize_list_response(data, response, "") is data


def test_resources_keep_existing_items():
    payload = {"data": [{"id": "resource-1", "type": "file", "file_id": "file-1"}]}
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    with Ark(http_client=httpx.Client(transport=transport)) as client:
        result = client.sessions.resources.list("session-1")
        assert result.data[0].id == "resource-1"
        assert result.data[0].file_id == "file-1"


def test_null_data_keeps_pagination_fields():
    payload = {"data": None, "first_id": "cursor", "last_id": "cursor", "has_more": True}
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json=payload))
    with Ark(http_client=httpx.Client(transport=transport)) as client:
        result = client.files.list()
        assert result.data == []
        assert result.first_id == result.last_id == "cursor"
        assert result.has_more is True
