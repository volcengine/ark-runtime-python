# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from arkruntime.resources.sessions.sessions import AsyncSessions, Sessions
from arkruntime.types.session.agent_with_upgrades import AgentWithUpgrades
from arkruntime.types.session.environment_with_upgrades import EnvironmentWithUpgrades
from arkruntime.types.session.managed_agents_text_block import ManagedAgentsTextBlock
from arkruntime.types.session.managed_agents_user_message_event_params import (
    ManagedAgentsUserMessageEventParams,
)


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


def test_upgrade_session_posts_upgrade_request() -> None:
    client = _SyncClient()
    Sessions(client).upgrade(
        "sess-1",
        agent=AgentWithUpgrades(type="agent_with_upgrades", id="agent-1", tools=[]),
        vault_ids=[],
    )

    assert client.request is not None
    assert client.request["args"] == ("/sessions/sess-1/upgrades",)
    assert client.request["body"] == {
        "agent": {
            "type": "agent_with_upgrades",
            "id": "agent-1",
            "tools": [],
        },
        "vault_ids": [],
    }


def test_upgrade_session_requires_session_id() -> None:
    with pytest.raises(ValueError, match="session_id"):
        Sessions(_SyncClient()).upgrade("")


def test_upgrade_session_serializes_environment_and_initial_events() -> None:
    client = _SyncClient()
    Sessions(client).upgrade(
        "sess-1",
        environment=EnvironmentWithUpgrades(type="environment_with_upgrades", id="env-1"),
        initial_events=[
            ManagedAgentsUserMessageEventParams(
                type="user.message",
                content=[ManagedAgentsTextBlock(type="text", text="/compact")],
            )
        ],
    )

    assert client.request is not None
    assert client.request["body"] == {
        "environment": {"type": "environment_with_upgrades", "id": "env-1"},
        "initial_events": [
            {
                "type": "user.message",
                "content": [{"type": "text", "text": "/compact"}],
            }
        ],
    }


@pytest.mark.asyncio
async def test_async_upgrade_session_posts_upgrade_request() -> None:
    client = _AsyncClient()
    await AsyncSessions(client).upgrade("sess-1", vault_ids=[])

    assert client.request is not None
    assert client.request["args"] == ("/sessions/sess-1/upgrades",)
    assert client.request["body"] == {"vault_ids": []}


@pytest.mark.asyncio
async def test_async_upgrade_session_requires_session_id() -> None:
    with pytest.raises(ValueError, match="session_id"):
        await AsyncSessions(_AsyncClient()).upgrade("")
