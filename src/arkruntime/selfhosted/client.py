# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import contextlib
import json
import math
import os
import random
import time
from dataclasses import replace
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import quote

import httpx

from arkruntime import Ark
from arkruntime._constants import CLIENT_REQUEST_HEADER, SERVER_REQUEST_HEADER
from arkruntime._types import NOT_GIVEN

from .types import (
    EXPECTED_LAST_HEARTBEAT_NO_HEARTBEAT,
    APIError,
    Event,
    HeartbeatResponse,
    ListEventsResponse,
    Session,
    SkillContent,
    SkillRef,
    WorkItem,
)

RETRYABLE_STATUS_CODES = {408, 409, 429}
RETRY_COUNT_HEADER = "X-Stainless-Retry-Count"
SKILL_TYPE_SKILL_HUB = "skill_hub"
SKILL_HUB_BASE_URL = "https://skills.volces.com/v1/skills"
MAX_SKILL_HUB_METADATA_BYTES = 1 << 20
SENSITIVE_EXTERNAL_HEADERS = (
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "x-ark-api-key",
)


class ClientAPI:
    """Adapter from the public Ark client to the self-hosted worker API."""

    def __init__(self, client: Ark) -> None:
        if client is None:
            raise ValueError("ark client is required")
        self.client = client

    def poll_work(
        self,
        environment_id: str,
        *,
        worker_id: str = "",
        block_ms: Optional[int] = 999,
        reclaim_older_than_ms: int = 0,
    ) -> Optional[WorkItem]:
        if not environment_id:
            raise ValueError("environment_id is required")
        item = self.client.environments.work.poll(
            environment_id,
            worker_id=worker_id,
            block_ms=block_ms,
            reclaim_older_than_ms=reclaim_older_than_ms,
            timeout=max(5.0, (block_ms or 0) / 1000.0 + 5.0),
        )
        if item is None:
            return None
        return item

    def ack_work(self, environment_id: str, work_id: str, *, worker_id: str = "") -> None:
        if not environment_id:
            raise ValueError("environment_id is required")
        if not work_id:
            raise ValueError("work_id is required")
        self.client.environments.work.ack(
            environment_id,
            work_id,
            worker_id=worker_id,
            timeout=10.0,
        )

    def heartbeat_work(
        self,
        environment_id: str,
        work_id: str,
        *,
        expected_last_heartbeat: str,
        desired_ttl_seconds: int = 30,
    ) -> HeartbeatResponse:
        if not environment_id:
            raise ValueError("environment_id is required")
        if not work_id:
            raise ValueError("work_id is required")
        response = self.client.environments.work.heartbeat(
            environment_id,
            work_id,
            expected_last_heartbeat=(expected_last_heartbeat or EXPECTED_LAST_HEARTBEAT_NO_HEARTBEAT),
            desired_ttl_seconds=desired_ttl_seconds,
            timeout=max(1.0, min(float(desired_ttl_seconds or 30) / 2, 30.0)),
        )
        return response

    def stop_work(self, environment_id: str, work_id: str, *, force: bool = False) -> None:
        if not environment_id:
            raise ValueError("environment_id is required")
        if not work_id:
            raise ValueError("work_id is required")
        self.client.environments.work.stop(
            environment_id,
            work_id,
            force=force,
            timeout=10.0,
        )

    def get_session(self, session_id: str) -> Session:
        if not session_id:
            raise ValueError("session_id is required")
        raw = _model_to_dict(self.client.sessions.retrieve(session_id, timeout=30.0))
        return Session.from_mapping(raw)

    def list_events(
        self,
        session_id: str,
        *,
        created_at_gt: str = "",
        page: str = "",
        limit: int = 100,
        order: str = "asc",
        types: Optional[List[str]] = None,
    ) -> ListEventsResponse:
        if not session_id:
            raise ValueError("session_id is required")
        resp = self.client.sessions.events.list(
            session_id,
            created_at_gt=created_at_gt if created_at_gt else NOT_GIVEN,
            page=page if page else NOT_GIVEN,
            limit=limit if limit > 0 else NOT_GIVEN,
            order=order if order else NOT_GIVEN,
            types=types if types else NOT_GIVEN,
            timeout=30.0,
        )
        return ListEventsResponse(
            events=[_event_from_model(event) for event in getattr(resp, "events", []) or []],
            next_page=getattr(resp, "next_page", "") or "",
        )

    def stream_events(self, session_id: str, *, timeout: Optional[float] = 30.0) -> Iterator[Event]:
        if not session_id:
            raise ValueError("session_id is required")
        for frame in self.client.sessions.events.stream(session_id, timeout=timeout):
            yield _event_from_model(getattr(frame, "data", None))

    def send_event(self, session_id: str, event: Event) -> None:
        if not session_id:
            raise ValueError("session_id is required")
        self._request_json(
            "POST",
            f"/sessions/{_escape(session_id)}/events",
            json={"events": [event.to_dict()]},
            timeout=15.0,
            max_retries=0,
        )

    def resolve_skill(self, skill: SkillRef) -> SkillRef:
        """Enrich a session skill reference with control-plane metadata."""
        skill_id = skill.id_value().strip()
        if not skill_id:
            raise ValueError("skill id is required")
        metadata = self.client.skills.retrieve(skill_id)
        name = str(getattr(metadata, "name", "") or "").strip()
        if not name:
            raise ValueError(f"skill name is empty: {skill_id}")
        return replace(
            skill,
            name=name,
            version=skill.version or str(getattr(metadata, "latest_version", "") or "").strip(),
        )

    def open_skill(self, session_id: str, skill: SkillRef) -> SkillContent:
        if skill.download_url:
            return self._open_external_skill(skill.download_url)
        skill_id = skill.id_value()
        if not skill_id:
            raise ValueError("skill id is required")
        if not skill.version:
            raise ValueError("skill version is required")
        if skill.type.strip().lower() == SKILL_TYPE_SKILL_HUB:
            slug = self._lookup_skill_hub_slug(skill_id)
            return self._open_external_skill(self._skill_hub_download_url(slug, skill.version))
        response = self.client._client.stream(
            "GET",
            self._url(f"/skills/{_escape(skill_id)}/versions/{_escape(skill.version)}/content"),
            headers=self._headers(),
        )
        resp = response.__enter__()
        try:
            self._raise_for_response(resp)
        except BaseException:
            response.__exit__(*os.sys.exc_info())
            raise
        return SkillContent(
            body=_ClosingStream(response, resp),
            content_length=int(resp.headers.get("content-length") or -1),
            file_name=os.path.basename(str(resp.request.url.path)),
            content_type=resp.headers.get("content-type", ""),
        )

    def _lookup_skill_hub_slug(self, skill_id: str) -> str:
        request = self._external_request(
            SKILL_HUB_BASE_URL,
            params={"skillIds": skill_id},
        )
        try:
            response = self.client._client.send(request, stream=True, follow_redirects=True)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise APIError(0, f"lookup skill hub metadata: {exc}", "") from exc
        try:
            self._raise_for_response(response)
            body = bytearray()
            for chunk in response.iter_bytes(chunk_size=65536):
                body.extend(chunk)
                if len(body) > MAX_SKILL_HUB_METADATA_BYTES:
                    raise APIError(response.status_code, "skill hub metadata response is too large", "")
            try:
                payload = json.loads(bytes(body))
            except (TypeError, ValueError) as exc:
                raise APIError(response.status_code, f"decode skill hub metadata: {exc}", "") from exc
        finally:
            response.close()
        skills = payload.get("Skills") if isinstance(payload, dict) else None
        for candidate in skills or []:
            if not isinstance(candidate, dict) or str(candidate.get("Id") or "").strip() != skill_id:
                continue
            slug = str(candidate.get("Slug") or "").strip().strip("/")
            if not slug:
                raise APIError(500, f"skill hub slug is empty: {skill_id}", "")
            return slug
        raise APIError(404, f"skill hub skill not found: {skill_id}", "")

    def _skill_hub_download_url(self, slug: str, version: str) -> str:
        segments = []
        for segment in slug.strip("/").split("/"):
            value = segment.strip()
            if not value or value in (".", ".."):
                raise ValueError(f"invalid skill hub slug: {slug!r}")
            segments.append(quote(value, safe=""))
        return str(
            httpx.URL(
                f"{SKILL_HUB_BASE_URL}/download/{'/'.join(segments)}",
                params={"version": version},
            )
        )

    def _open_external_skill(self, url: str) -> SkillContent:
        request = self._external_request(url)
        try:
            response = self.client._client.send(request, stream=True, follow_redirects=True)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise APIError(0, str(exc), "") from exc
        try:
            self._raise_for_response(response)
        except BaseException:
            response.close()
            raise
        return SkillContent(
            body=_ClosingStream(None, response),
            content_length=int(response.headers.get("content-length") or -1),
            file_name=os.path.basename(str(response.request.url.path)),
            content_type=response.headers.get("content-type", ""),
        )

    def _external_request(
        self,
        url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Request:
        request = self.client._client.build_request("GET", url, params=params)
        for header in SENSITIVE_EXTERNAL_HEADERS:
            request.headers.pop(header, None)
        return request

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        retry_count = getattr(self.client, "max_retries", 0) if max_retries is None else max_retries
        if isinstance(retry_count, float) and math.isinf(retry_count):
            retry_count = 2**63 - 1
        elif isinstance(retry_count, float) and math.isnan(retry_count):
            retry_count = 0
        retry_count = max(0, int(retry_count or 0))
        for attempt in range(retry_count + 1):
            try:
                request_options: Dict[str, Any] = {}
                if timeout is not None:
                    request_options["timeout"] = timeout
                request_headers = httpx.Headers(self._headers(headers))
                if RETRY_COUNT_HEADER not in request_headers:
                    request_headers[RETRY_COUNT_HEADER] = str(attempt)
                resp = self.client._client.request(
                    method,
                    self._url(path),
                    params=params or None,
                    headers=request_headers,
                    json=json,
                    **request_options,
                )
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt < retry_count:
                    self._sleep_retry(attempt, None)
                    continue
                raise APIError(0, str(exc), "") from exc
            if _should_retry(resp) and attempt < retry_count:
                if not resp.is_closed:
                    with contextlib.suppress(Exception):
                        resp.read()
                response_headers = resp.headers
                resp.close()
                self._sleep_retry(attempt, response_headers)
                continue
            break
        self._raise_for_response(resp)
        if not resp.content:
            return {}
        try:
            data = resp.json()
        except ValueError as exc:
            raise APIError(resp.status_code, str(exc), resp.headers.get(SERVER_REQUEST_HEADER, "")) from exc
        return data if isinstance(data, dict) else {}

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        headers.update(self.client.auth_headers or {})
        headers.update(extra or {})
        return headers

    def _url(self, path: str) -> str:
        return f"{str(self.client._base_url).rstrip('/')}/{path.lstrip('/')}"

    def _raise_for_response(self, resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return
        if not resp.is_closed:
            with contextlib.suppress(Exception):
                resp.read()
        request_id = resp.headers.get(SERVER_REQUEST_HEADER) or resp.headers.get(CLIENT_REQUEST_HEADER, "")
        try:
            err = self.client._make_status_error_from_response(resp, request_id=request_id)
        except Exception as exc:  # noqa: BLE001 - preserve status for worker classification.
            raise APIError(resp.status_code, str(exc), request_id) from exc
        raise APIError(resp.status_code, str(err), request_id) from err

    def _sleep_retry(self, attempt: int, response_headers: Optional[httpx.Headers]) -> None:
        retry_after = self.client._parse_retry_after_header(response_headers)
        if retry_after is not None and 0 < retry_after <= 60:
            time.sleep(retry_after)
            return
        delay = min(8.0, 0.5 * (2**attempt))
        time.sleep(delay * random.uniform(0.75, 1.0))


class _ClosingStream:
    def __init__(self, manager: Any, response: httpx.Response) -> None:
        self._manager = manager
        self._response = response
        self._iterator = response.iter_bytes(chunk_size=65536)

    def read(self, size: int = -1) -> bytes:
        if size is None or size < 0:
            return self._response.read()
        try:
            return next(self._iterator)
        except StopIteration:
            return b""

    def iter_bytes(self, chunk_size: int = 65536) -> Iterator[bytes]:
        yield from self._response.iter_bytes(chunk_size=chunk_size)

    def close(self) -> None:
        if self._manager is None:
            self._response.close()
            return
        self._manager.__exit__(None, None, None)


def _escape(value: str) -> str:
    return quote(value, safe="")


def _should_retry(response: httpx.Response) -> bool:
    should_retry = response.headers.get("x-should-retry")
    should_retry = should_retry.lower() if should_retry else None
    if should_retry == "true":
        return True
    if should_retry == "false":
        return False
    return response.status_code in RETRYABLE_STATUS_CODES or response.status_code >= 500


def _model_to_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", by_alias=True)
    if hasattr(value, "dict"):
        return value.dict(by_alias=True)
    if isinstance(value, dict):
        return value
    return {}


def _event_from_model(value: Any) -> Event:
    if value is None:
        return Event(type="")
    raw = _model_to_dict(value)
    if not raw and isinstance(value, dict):
        raw = value
    raw_payload = raw.get("raw_payload")
    if raw_payload and isinstance(raw_payload, str):
        try:
            parsed = json.loads(raw_payload)
            if isinstance(parsed, dict):
                raw = parsed
        except ValueError:
            pass
    return Event.from_mapping(raw)
