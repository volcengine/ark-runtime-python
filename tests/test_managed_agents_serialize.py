import json

import httpx
import pytest
from pydantic import ValidationError

from arkruntime import Ark
from arkruntime._managed_agents_serialize import dump_body
from arkruntime.types.agent import (
    ModelConfig,
    MultiagentPatch,
    MultiagentSubagentsConfig,
)


def test_multiagent_update_preserves_explicit_null_and_empty_array() -> None:
    body = dump_body(
        {
            "version": 1,
            "multiagent": MultiagentPatch(
                type="multiagent_20261001",
                subagents=MultiagentSubagentsConfig(
                    type="enabled",
                    inline_agents=None,
                    predefined_agents=[],
                ),
            ),
        }
    )

    assert json.loads(json.dumps(body)) == {
        "version": 1,
        "multiagent": {
            "type": "multiagent_20261001",
            "subagents": {
                "type": "enabled",
                "inline_agents": None,
                "predefined_agents": [],
            },
        },
    }


def test_multiagent_update_explicit_null_is_sent() -> None:
    assert dump_body({"version": 1, "multiagent": None}) == {
        "version": 1,
        "multiagent": None,
    }


def test_agent_update_wrapper_sends_explicit_multiagent_null() -> None:
    bodies = []

    def handle(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "agent-1",
                "type": "agent",
                "name": "agent",
                "version": 2,
                "created_at": "2026-10-28T00:00:00Z",
                "updated_at": "2026-10-28T00:00:00Z",
            },
        )

    with Ark(
        api_key="placeholder",
        http_client=httpx.Client(transport=httpx.MockTransport(handle)),
    ) as client:
        client.agents.update("agent-1", version=1, multiagent=None)

    assert bodies == [{"version": 1, "multiagent": None}]


@pytest.mark.parametrize(
    "multiagent",
    [
        {"type": "multiagent_20261001"},
        {"type": "multiagent_20261001", "subagents": None},
    ],
)
def test_agent_create_rejects_dynamic_multiagent_without_subagents(
    multiagent: dict,
) -> None:
    with Ark(api_key="placeholder") as client:
        with pytest.raises(ValidationError, match="multiagent.subagents"):
            client.agents.create(
                name="agent",
                model=ModelConfig(id="model-id"),
                multiagent=multiagent,
            )
