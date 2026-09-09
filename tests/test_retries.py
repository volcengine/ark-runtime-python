# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from email.utils import formatdate

import httpx

from arkruntime import Ark
from arkruntime._request_options import RequestOptions


def _test_credential() -> str:
    return "placeholder"


def _client(*, max_retries: int = 2) -> Ark:
    return Ark(
        api_key=_test_credential(),
        base_url="https://ark.example.com/api/v3",
        http_client=httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200))),
        max_retries=max_retries,
    )


def test_retry_after_ms_takes_priority() -> None:
    client = _client()
    try:
        headers = httpx.Headers({"Retry-After-Ms": "125.5", "Retry-After": "9"})
        assert client._parse_retry_after_header(headers) == 0.1255
    finally:
        client.close()


def test_retry_after_supports_fractional_seconds_and_http_date(monkeypatch) -> None:
    client = _client()
    try:
        assert client._parse_retry_after_header(httpx.Headers({"Retry-After": "0.25"})) == 0.25

        monkeypatch.setattr("arkruntime._base_client.time.time", lambda: 1_000.0)
        retry_date = formatdate(1_003.0, usegmt=True)
        assert client._parse_retry_after_header(httpx.Headers({"Retry-After": retry_date})) == 3.0
    finally:
        client.close()


def test_default_retry_backoff_starts_at_half_second(monkeypatch) -> None:
    client = _client()
    monkeypatch.setattr("arkruntime._base_client.random", lambda: 0.0)
    options = RequestOptions.construct(method="get", url="/sessions")
    try:
        assert client._calculate_retry_timeout(1, options) == 0.5
        assert client._calculate_retry_timeout(0, options) == 1.0
    finally:
        client.close()


def test_invalid_server_retry_delays_fall_back_to_backoff(monkeypatch) -> None:
    client = _client()
    monkeypatch.setattr("arkruntime._base_client.random", lambda: 0.0)
    options = RequestOptions.construct(method="get", url="/sessions")
    try:
        for value in ["0", "-1", "61", "Infinity", "NaN"]:
            headers = httpx.Headers({"Retry-After": value})
            assert client._calculate_retry_timeout(1, options, headers) == 0.5
    finally:
        client.close()


def test_retry_count_header_tracks_attempt_and_allows_override() -> None:
    client = _client()
    options = RequestOptions.construct(method="get", url="/sessions")
    overridden = RequestOptions.construct(
        method="get",
        url="/sessions",
        headers={"X-Stainless-Retry-Count": "custom"},
    )
    try:
        assert client._build_request(options, retries_taken=0).headers["x-stainless-retry-count"] == "0"
        assert client._build_request(options, retries_taken=2).headers["x-stainless-retry-count"] == "2"
        assert client._build_request(overridden, retries_taken=2).headers["x-stainless-retry-count"] == "custom"
    finally:
        client.close()


def test_zero_per_request_max_retries_is_preserved() -> None:
    client = _client(max_retries=2)
    options = RequestOptions.construct(method="get", url="/sessions", max_retries=0)
    try:
        assert client._remaining_retries(None, options) == 0
    finally:
        client.close()


def test_sync_request_uses_server_delay_and_increments_retry_count(monkeypatch) -> None:
    retry_counts = []
    calls = 0

    def handle(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        retry_counts.append(request.headers["x-stainless-retry-count"])
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After-Ms": "10"}, request=request)
        return httpx.Response(200, json={}, request=request)

    sleeps = []
    monkeypatch.setattr("arkruntime._base_client.time.sleep", sleeps.append)
    client = Ark(
        api_key=_test_credential(),
        base_url="https://ark.example.com/api/v3",
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
        max_retries=2,
    )
    try:
        assert client.get("/retry", cast_to=object) == {}
    finally:
        client.close()

    assert retry_counts == ["0", "1"]
    assert sleeps == [0.01]


def test_post_without_retry_marks_request_as_initial_attempt() -> None:
    retry_counts = []

    def handle(request: httpx.Request) -> httpx.Response:
        retry_counts.append(request.headers["x-stainless-retry-count"])
        return httpx.Response(500, request=request)

    client = Ark(
        api_key=_test_credential(),
        base_url="https://ark.example.com/api/v3",
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
        max_retries=2,
    )
    try:
        try:
            client.post_without_retry("/single", cast_to=object)
        except Exception:
            pass
        else:
            raise AssertionError("expected request failure")
    finally:
        client.close()

    assert retry_counts == ["0"]


def test_should_retry_header_is_case_insensitive() -> None:
    client = _client()
    request = httpx.Request("GET", "https://ark.example.com")
    try:
        assert client._should_retry(httpx.Response(400, headers={"X-Should-Retry": "TRUE"}, request=request))
        assert not client._should_retry(httpx.Response(500, headers={"X-Should-Retry": "False"}, request=request))
    finally:
        client.close()


def test_conflict_is_retried_by_default() -> None:
    client = _client()
    request = httpx.Request("GET", "https://ark.example.com")
    try:
        assert client._should_retry(httpx.Response(409, request=request))
        assert not client._should_retry(httpx.Response(409, headers={"X-Should-Retry": "false"}, request=request))
    finally:
        client.close()
