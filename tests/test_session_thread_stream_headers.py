from uuid import uuid4

import httpx
import pytest

from arkruntime.resources.sessions.session_threads import (
    AsyncSessionThreads,
    SessionThreads,
)


class _SyncClient:
    def __init__(self, transport) -> None:
        self._client = httpx.Client(transport=transport)
        self._base_url = "https://api.example.com"

    def default_headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ark-runtime-test",
            "X-Client-Request-Id": "request-id",
            "X-Ark-Env": "lane-test",
            "X-Maas-Env": "multiagent",
        }

    def post(self, *args, **kwargs):
        raise AssertionError("stream tests do not use JSON requests")

    get = post
    delete = post
    post_without_retry = post
    get_api_list = post


class _AsyncClient:
    def __init__(self, transport) -> None:
        self._client = httpx.AsyncClient(transport=transport)
        self._base_url = "https://api.example.com"

    def default_headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ark-runtime-test",
            "X-Client-Request-Id": "request-id",
            "X-Ark-Env": "lane-test",
            "X-Maas-Env": "multiagent",
        }

    def post(self, *args, **kwargs):
        raise AssertionError("stream tests do not use JSON requests")

    get = post
    delete = post
    post_without_retry = post
    get_api_list = post


def _assert_stream_headers(request: httpx.Request) -> None:
    assert request.headers["Accept"] == "text/event-stream"
    assert request.headers["User-Agent"] == "ark-runtime-test"
    assert request.headers["X-Client-Request-Id"] == "request-id"
    assert request.headers["X-Ark-Env"] == "lane-test"
    assert request.headers["X-Maas-Env"] == "multiagent"


def test_session_thread_stream_propagates_default_headers() -> None:
    session_id = str(uuid4())
    thread_id = str(uuid4())
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text="")

    client = _SyncClient(httpx.MockTransport(handle))
    assert list(SessionThreads(client).stream(session_id, thread_id)) == []
    client._client.close()

    assert len(requests) == 1
    _assert_stream_headers(requests[0])


@pytest.mark.asyncio
async def test_async_session_thread_stream_propagates_default_headers() -> None:
    session_id = str(uuid4())
    thread_id = str(uuid4())
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text="")

    client = _AsyncClient(httpx.MockTransport(handle))
    assert [frame async for frame in AsyncSessionThreads(client).stream(session_id, thread_id)] == []
    await client._client.aclose()

    assert len(requests) == 1
    _assert_stream_headers(requests[0])
