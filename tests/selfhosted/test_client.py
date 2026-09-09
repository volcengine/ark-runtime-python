# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import math

import httpx

from arkruntime import Ark
from arkruntime.selfhosted import APIError, ClientAPI, SkillRef
from arkruntime.selfhosted.types import work_session_id


def _test_credential() -> str:
    return "placeholder"


def _ark_client(transport: httpx.MockTransport, *, max_retries: int = 0) -> Ark:
    return Ark(
        api_key=_test_credential(),
        base_url="https://ark.example.com/api/v3",
        http_client=httpx.Client(
            transport=transport,
            headers={"Authorization": "Bearer inherited-test-key"},
        ),
        max_retries=max_retries,
    )


def test_selfhosted_event_stream_has_default_read_inactivity_timeout() -> None:
    seen = []

    class Events:
        def stream(self, session_id, *, timeout):
            seen.append((session_id, timeout))
            return iter(())

    class Sessions:
        events = Events()

    class Client:
        sessions = Sessions()

    list(ClientAPI(Client()).stream_events("session-1"))

    assert seen == [("session-1", 30.0)]


def test_poll_work_preserves_nested_session_data() -> None:
    work = {
        "id": "sesn-20260814050521-zb4l4",
        "created_at": "2026-08-14T05:05:21Z",
        "data": {
            "id": "sesn-20260814050521-zb4l4",
            "type": "session",
        },
        "environment_id": "env-20260813132936-wq8d4",
        "state": "queued",
        "type": "work",
    }

    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/environments/env-20260813132936-wq8d4/work/poll"
        return httpx.Response(httpx.codes.OK, json=work)

    client = _ark_client(httpx.MockTransport(handle))
    try:
        item = ClientAPI(client).poll_work("env-20260813132936-wq8d4")
    finally:
        client.close()

    assert item is not None
    assert item.id == work["id"]
    assert item.data.id == work["data"]["id"]
    assert item.data.type == "session"
    assert work_session_id(item) == work["data"]["id"]


def test_poll_work_can_omit_block_ms_for_nonblocking_drain() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert "block_ms" not in request.url.params
        return httpx.Response(httpx.codes.OK, json={})

    client = _ark_client(httpx.MockTransport(handle))
    try:
        assert ClientAPI(client).poll_work("env-1", block_ms=None) is None
    finally:
        client.close()


def test_poll_work_rejects_payload_outside_generated_contract() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(httpx.codes.OK, json={"id": "work-without-required-fields"})

    client = _ark_client(httpx.MockTransport(handle))
    try:
        try:
            ClientAPI(client).poll_work("env-1")
        except Exception as exc:
            assert "invalid WorkItem response" in str(exc)
        else:
            raise AssertionError("expected generated model validation failure")
    finally:
        client.close()


def test_heartbeat_uses_generated_response_model() -> None:
    heartbeat = {
        "last_heartbeat": "2026-08-24T10:00:00Z",
        "lease_extended": True,
        "state": "active",
        "ttl_seconds": 30,
        "type": "work_heartbeat",
    }

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(httpx.codes.OK, json=heartbeat)

    client = _ark_client(httpx.MockTransport(handle))
    try:
        response = ClientAPI(client).heartbeat_work(
            "env-1",
            "work-1",
            expected_last_heartbeat="NO_HEARTBEAT",
            desired_ttl_seconds=30,
        )
    finally:
        client.close()

    assert response.last_heartbeat == heartbeat["last_heartbeat"]
    assert response.lease_extended is True
    assert response.state == "active"
    assert response.ttl_seconds == 30


def test_atomic_environment_work_api_matches_openapi_contract() -> None:
    work = {
        "id": "work-1",
        "created_at": "2026-08-24T10:00:00Z",
        "data": {"id": "test", "type": "session"},
        "environment_id": "env-1",
        "state": "active",
        "type": "work",
    }
    heartbeat = {
        "last_heartbeat": "2026-08-24T10:00:01Z",
        "lease_extended": True,
        "state": "active",
        "ttl_seconds": 30,
        "type": "work_heartbeat",
    }
    calls = []

    def handle(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/poll"):
            assert request.method == "GET"
            assert request.url.params["block_ms"] == "999"
            assert request.url.params["reclaim_older_than_ms"] == "5000"
            assert request.headers["Ark-Worker-ID"] == "worker-1"
            return httpx.Response(httpx.codes.OK, json=work)
        if request.url.path.endswith("/ack"):
            assert request.method == "POST"
            assert request.headers["Ark-Worker-ID"] == "worker-1"
            return httpx.Response(httpx.codes.OK, json=work)
        if request.url.path.endswith("/heartbeat"):
            assert request.method == "POST"
            assert request.url.params["expected_last_heartbeat"] == "NO_HEARTBEAT"
            assert request.url.params["desired_ttl_seconds"] == "30"
            return httpx.Response(httpx.codes.OK, json=heartbeat)
        assert request.url.path.endswith("/stop")
        assert request.method == "POST"
        assert request.content == b"{}"
        return httpx.Response(httpx.codes.OK, json=work)

    client = _ark_client(httpx.MockTransport(handle))
    try:
        resource = client.environments.work
        assert (
            resource.poll(
                "env-1",
                worker_id="worker-1",
                block_ms=999,
                reclaim_older_than_ms=5000,
            ).id
            == "work-1"
        )
        assert resource.ack("env-1", "work-1", worker_id="worker-1").id == "work-1"
        assert (
            resource.heartbeat(
                "env-1",
                "work-1",
                expected_last_heartbeat="NO_HEARTBEAT",
                desired_ttl_seconds=30,
            ).lease_extended
            is True
        )
        assert resource.stop("env-1", "work-1").id == "work-1"
    finally:
        client.close()

    assert [request.url.path for request in calls] == [
        "/api/v3/environments/env-1/work/poll",
        "/api/v3/environments/env-1/work/work-1/ack",
        "/api/v3/environments/env-1/work/work-1/heartbeat",
        "/api/v3/environments/env-1/work/work-1/stop",
    ]


def test_list_events_decodes_wire_data_into_tool_use_events() -> None:
    tool_use = {
        "id": "call_test",
        "type": "agent.tool_use",
        "name": "bash",
        "input": {"command": "python --version"},
        "session_thread_id": "sthr_test",
    }

    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/sessions/sesn_test/events"
        assert request.url.params["limit"] == "100"
        assert request.url.params["order"] == "asc"
        return httpx.Response(httpx.codes.OK, json={"data": [tool_use]})

    http_client = httpx.Client(transport=httpx.MockTransport(handle))
    client = Ark(
        api_key=_test_credential(),
        base_url="https://ark.example.com/api/v3",
        http_client=http_client,
    )
    try:
        response = ClientAPI(client).list_events("sesn_test")
    finally:
        client.close()

    assert len(response.events) == 1
    event = response.events[0]
    assert event.id == tool_use["id"]
    assert event.type == tool_use["type"]
    assert event.name == tool_use["name"]
    assert event.input == tool_use["input"]
    assert event.session_thread_id == tool_use["session_thread_id"]


def test_resolve_skill_uses_control_plane_metadata() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v3/skills/skill-1"
        return httpx.Response(
            httpx.codes.OK,
            json={
                "id": "skill-1",
                "object": "skill",
                "created_at": 1786506774,
                "name": "canonical-skill-name",
                "latest_version": "1.0.0",
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handle))
    client = Ark(
        api_key=_test_credential(),
        base_url="https://ark.example.com/api/v3",
        http_client=http_client,
    )
    try:
        resolved = ClientAPI(client).resolve_skill(SkillRef(skill_id="skill-1", type="skill_hub"))
    finally:
        client.close()

    assert resolved.name == "canonical-skill-name"
    assert resolved.version == "1.0.0"
    assert resolved.type == "skill_hub"


def test_open_skill_hub_resolves_metadata_and_downloads_version() -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        requests.append(request.url)
        if request.url.path == "/v1/skills":
            assert request.url.params["skillIds"] == "skill-1"
            return httpx.Response(
                httpx.codes.OK,
                json={
                    "Skills": [
                        {"Id": "other-skill", "Slug": "wrong/slug"},
                        {"Id": "skill-1", "Slug": "volcengine/ark/demo"},
                    ],
                    "Total": 2,
                },
            )
        assert request.url.path == "/v1/skills/download/volcengine/ark/demo"
        assert request.url.params["version"] == "1.0.0"
        return httpx.Response(
            httpx.codes.OK,
            content=b"skill-hub-zip",
            headers={"Content-Type": "application/zip"},
        )

    client = _ark_client(httpx.MockTransport(handle))
    try:
        content = ClientAPI(client).open_skill(
            "test",
            SkillRef(type="skill_hub", skill_id="skill-1", version="1.0.0"),
        )
        try:
            assert content.body.read() == b"skill-hub-zip"
        finally:
            content.body.close()
    finally:
        client.close()

    assert len(requests) == 2


def test_heartbeat_has_lease_bounded_timeout_and_no_hidden_retry() -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.extensions["timeout"]["read"] == 15.0
        assert request.headers["x-stainless-retry-count"] == "0"
        return httpx.Response(httpx.codes.INTERNAL_SERVER_ERROR, json={"error": "temporary"})

    client = _ark_client(httpx.MockTransport(handle), max_retries=3)
    try:
        try:
            ClientAPI(client).heartbeat_work(
                "env-1",
                "work-1",
                expected_last_heartbeat="NO_HEARTBEAT",
                desired_ttl_seconds=30,
            )
        except Exception:
            pass
        else:
            raise AssertionError("expected heartbeat failure")
    finally:
        client.close()

    assert len(requests) == 1


def test_raw_request_supports_infinite_retry_configuration() -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(httpx.codes.OK, json={})

    client = _ark_client(httpx.MockTransport(handle), max_retries=math.inf)  # type: ignore[arg-type]
    try:
        assert ClientAPI(client)._request_json("GET", "/test") == {}
    finally:
        client.close()

    assert len(requests) == 1


def test_raw_request_retry_header_is_case_insensitive() -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(400, headers={"X-Should-Retry": "TRUE", "Retry-After-Ms": "1"})
        return httpx.Response(httpx.codes.OK, json={})

    client = _ark_client(httpx.MockTransport(handle), max_retries=1)
    try:
        assert ClientAPI(client)._request_json("GET", "/test") == {}
    finally:
        client.close()

    assert len(requests) == 2


def test_raw_request_retries_conflict_by_default() -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(409, json={"error": {"message": "conflict"}})

    client = _ark_client(httpx.MockTransport(handle), max_retries=1)
    try:
        try:
            ClientAPI(client)._request_json("GET", "/test")
        except APIError:
            pass
        else:
            raise AssertionError("expected request failure")
    finally:
        client.close()

    assert len(requests) == 2
