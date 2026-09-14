# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Tests for the hand-written checkpoint / restore / agent-version call layer.

The generated ``types/session/*`` models are covered by the ark-apis
codegen contract; these tests pin the request wiring (URL, query
encoding, NOT_GIVEN omission) of the resource wrappers.
"""

from __future__ import annotations

import pytest

from arkruntime.resources.agents.agents import Agents, AsyncAgents
from arkruntime.resources.checkpoints import AsyncCheckpoints, Checkpoints
from arkruntime.resources.sessions.sessions import AsyncSessions, Sessions
from arkruntime.types.session.checkpoint_restore_config import CheckpointRestoreConfig
from arkruntime.types.session.checkpoint_status import CheckpointStatus


class _SyncClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def _record(self, method: str, *args: object, **kwargs: object) -> dict[str, object]:
        call = {"method": method, "args": args, **kwargs}
        self.calls.append(call)
        return call

    def post(self, *args: object, **kwargs: object) -> dict[str, object]:
        return self._record("POST", *args, **kwargs)

    def post_without_retry(self, *args: object, **kwargs: object) -> dict[str, object]:
        return self._record("POST", *args, **kwargs)

    def get(self, *args: object, **kwargs: object) -> dict[str, object]:
        return self._record("GET", *args, **kwargs)

    def delete(self, *args: object, **kwargs: object) -> dict[str, object]:
        return self._record("DELETE", *args, **kwargs)

    def get_api_list(self, *args: object, **kwargs: object) -> list[object]:
        return []


class _AsyncClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def _record(self, method: str, *args: object, **kwargs: object) -> dict[str, object]:
        call = {"method": method, "args": args, **kwargs}
        self.calls.append(call)
        return call

    async def post(self, *args: object, **kwargs: object) -> dict[str, object]:
        return await self._record("POST", *args, **kwargs)

    async def post_without_retry(self, *args: object, **kwargs: object) -> dict[str, object]:
        return await self._record("POST", *args, **kwargs)

    async def get(self, *args: object, **kwargs: object) -> dict[str, object]:
        return await self._record("GET", *args, **kwargs)

    async def delete(self, *args: object, **kwargs: object) -> dict[str, object]:
        return await self._record("DELETE", *args, **kwargs)

    async def get_api_list(self, *args: object, **kwargs: object) -> list[object]:
        return []


# --- Checkpoints.create ---------------------------------------------------


def test_create_checkpoint_posts_to_session_subresource() -> None:
    client = _SyncClient()
    Checkpoints(client).create("sess-1", name="nightly")

    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["args"] == ("/sessions/sess-1/checkpoints",)
    assert call["body"] == {"name": "nightly"}


def test_create_checkpoint_requires_session_id() -> None:
    with pytest.raises(ValueError, match="session_id"):
        Checkpoints(_SyncClient()).create("", name="nightly")


@pytest.mark.asyncio
async def test_async_create_checkpoint() -> None:
    client = _AsyncClient()
    await AsyncCheckpoints(client).create("sess-1", name="nightly")

    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["args"] == ("/sessions/sess-1/checkpoints",)
    assert call["body"] == {"name": "nightly"}


# --- Checkpoints.list -----------------------------------------------------


def test_list_checkpoints_encodes_filters_as_repeated_query() -> None:
    client = _SyncClient()
    Checkpoints(client).list(
        source_session_id="sess-1",
        status=[CheckpointStatus.ready, CheckpointStatus.failed],
        limit=10,
        page="cursor-1",
    )

    call = client.calls[0]
    assert call["method"] == "GET"
    assert call["args"] == ("/checkpoints",)
    assert call["options"]["params"] == {
        "source_session_id": "sess-1",
        "status": [CheckpointStatus.ready, CheckpointStatus.failed],
        "limit": 10,
        "page": "cursor-1",
    }


def test_list_checkpoints_defaults_to_empty_query() -> None:
    client = _SyncClient()
    Checkpoints(client).list()

    call = client.calls[0]
    assert call["args"] == ("/checkpoints",)
    assert call["options"]["params"] == {}


def test_list_checkpoints_drops_explicit_none_filters() -> None:
    client = _SyncClient()
    Checkpoints(client).list(source_session_id=None, status=None, limit=None, page=None)

    assert client.calls[0]["options"]["params"] == {}


@pytest.mark.asyncio
async def test_async_list_checkpoints() -> None:
    client = _AsyncClient()
    await AsyncCheckpoints(client).list(status=[CheckpointStatus.ready])

    assert client.calls[0]["options"]["params"] == {"status": [CheckpointStatus.ready]}


# --- Checkpoints.retrieve / delete ----------------------------------------


def test_retrieve_checkpoint() -> None:
    client = _SyncClient()
    Checkpoints(client).retrieve("cp-1")

    call = client.calls[0]
    assert call["method"] == "GET"
    assert call["args"] == ("/checkpoints/cp-1",)


def test_retrieve_checkpoint_requires_id() -> None:
    with pytest.raises(ValueError, match="checkpoint_id"):
        Checkpoints(_SyncClient()).retrieve("")


def test_delete_checkpoint() -> None:
    client = _SyncClient()
    Checkpoints(client).delete("cp-1")

    call = client.calls[0]
    assert call["method"] == "DELETE"
    assert call["args"] == ("/checkpoints/cp-1",)


def test_delete_checkpoint_requires_id() -> None:
    with pytest.raises(ValueError, match="checkpoint_id"):
        Checkpoints(_SyncClient()).delete("")


@pytest.mark.asyncio
async def test_async_retrieve_and_delete_checkpoint() -> None:
    client = _AsyncClient()
    await AsyncCheckpoints(client).retrieve("cp-1")
    await AsyncCheckpoints(client).delete("cp-1")

    assert client.calls[0]["args"] == ("/checkpoints/cp-1",)
    assert client.calls[0]["method"] == "GET"
    assert client.calls[1]["args"] == ("/checkpoints/cp-1",)
    assert client.calls[1]["method"] == "DELETE"


# --- Sessions.create restore wiring ---------------------------------------


def test_create_session_from_checkpoint_omits_unrelated_fields() -> None:
    client = _SyncClient()
    Sessions(client).create(checkpoint_id="cp-1")

    call = client.calls[0]
    assert call["args"] == ("/sessions",)
    # NOT_GIVEN fields (agent / environment_id / resources / ...) must not
    # hit the wire — the server rejects resources on restore and inherits
    # agent/environment from the snapshot when omitted.
    assert call["body"] == {"checkpoint_id": "cp-1"}


def test_create_session_from_checkpoint_with_restore_config() -> None:
    client = _SyncClient()
    Sessions(client).create(
        checkpoint_id="cp-1",
        checkpoint_restore_config=CheckpointRestoreConfig(tos_bucket="target-bkt"),
    )

    assert client.calls[0]["body"] == {
        "checkpoint_id": "cp-1",
        "checkpoint_restore_config": {"tos_bucket": "target-bkt"},
    }


def test_create_session_normal_path_unchanged() -> None:
    client = _SyncClient()
    Sessions(client).create(agent="agent-1", environment_id="env-1", title="plain")

    body = client.calls[0]["body"]
    assert body["agent"] == "agent-1"
    assert body["environment_id"] == "env-1"
    assert body["title"] == "plain"
    assert "checkpoint_id" not in body
    assert "checkpoint_restore_config" not in body


@pytest.mark.asyncio
async def test_async_create_session_from_checkpoint() -> None:
    client = _AsyncClient()
    await AsyncSessions(client).create(checkpoint_id="cp-1")

    assert client.calls[0]["body"] == {"checkpoint_id": "cp-1"}


# --- Agents.retrieve version query ----------------------------------------


def test_retrieve_agent_with_version() -> None:
    client = _SyncClient()
    Agents(client).retrieve("agent-1", version=3)

    call = client.calls[0]
    assert call["method"] == "GET"
    assert call["args"] == ("/agents/agent-1",)
    assert call["options"]["params"] == {"version": 3}


def test_retrieve_agent_without_version_has_no_query() -> None:
    client = _SyncClient()
    Agents(client).retrieve("agent-1")

    assert "params" not in client.calls[0]["options"]


def test_retrieve_agent_requires_id() -> None:
    with pytest.raises(ValueError, match="agent_id"):
        Agents(_SyncClient()).retrieve("", version=1)


@pytest.mark.asyncio
async def test_async_retrieve_agent_with_version() -> None:
    client = _AsyncClient()
    await AsyncAgents(client).retrieve("agent-1", version=7)

    assert client.calls[0]["options"]["params"] == {"version": 7}
