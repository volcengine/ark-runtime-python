import json
from importlib.metadata import version

import httpx
import pytest

from arkruntime import Ark, AsyncArk
from arkruntime._constants import CLIENT_REQUEST_HEADER
from arkruntime.resources.sessions.session_events import _decode_stream_frame
from arkruntime.types.session import ManagedAgentsAgentCustomToolUseEvent


def _assert_stream_headers(request: httpx.Request) -> None:
    assert request.headers["Accept"] == "text/event-stream"
    assert request.headers["Authorization"] == "Bearer placeholder"
    assert request.headers["X-Ark-Env"] == "lane-test"
    assert request.headers["X-Maas-Env"] == "multiagent"
    assert request.headers["User-Agent"] == "ark-runtime-python/" + version("arkruntime")
    assert request.headers[CLIENT_REQUEST_HEADER]


def test_session_stream_propagates_sdk_default_headers() -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text="")

    with Ark(
        api_key="placeholder",
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    ) as client:
        client._custom_headers.update({"X-Ark-Env": "lane-test", "X-Maas-Env": "multiagent"})
        assert list(client.sessions.events.stream("session-1")) == []

    assert len(requests) == 1
    _assert_stream_headers(requests[0])


@pytest.mark.asyncio
async def test_async_session_stream_propagates_sdk_default_headers() -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, text="")

    async with AsyncArk(
        api_key="placeholder",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle)),
    ) as client:
        client._custom_headers.update({"X-Ark-Env": "lane-test", "X-Maas-Env": "multiagent"})
        assert [frame async for frame in client.sessions.events.stream("session-1")] == []

    assert len(requests) == 1
    _assert_stream_headers(requests[0])


def test_session_stream_decodes_child_custom_tool_use_event() -> None:
    payload = {
        "type": "agent.custom_tool_use",
        "id": "event-1",
        "processed_at": "2026-10-11T00:00:00Z",
        "session_thread_id": "thread-child",
        "custom_tool_use_id": "call-1",
        "name": "submit",
        "input": {"text": "hello"},
    }

    frame = _decode_stream_frame("", json.dumps(payload))
    event = frame.data

    assert frame.type == "agent.custom_tool_use"
    assert isinstance(event, ManagedAgentsAgentCustomToolUseEvent)
    assert event.id == "event-1"
    assert event.custom_tool_use_id == "call-1"
    assert event.session_thread_id == "thread-child"
    assert event.name == "submit"
    assert event.input == {"text": "hello"}
