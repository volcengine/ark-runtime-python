import os
import time

import pytest

from arkruntime import Ark
from arkruntime.types.agent import (
    AgentRef,
    ModelConfig,
    MultiagentConfig,
    MultiagentPatch,
    MultiagentSubagentsConfig,
)


@pytest.mark.skipif(
    not os.environ.get("ARK_STG_TOKEN") or not os.environ.get("ARK_E2E_BASE_URL"),
    reason="ARK_STG_TOKEN and ARK_E2E_BASE_URL are required for Managed Agents E2E",
)
def test_multiagent_client_gate_against_stg() -> None:
    client = Ark(
        api_key=os.environ["ARK_STG_TOKEN"],
        base_url=os.environ["ARK_E2E_BASE_URL"],
        max_retries=0,
    )
    name = f"sdk-gate-py-{int(time.time() * 1000)}"
    created = None
    try:
        created = client.agents.create(
            name=name,
            model=ModelConfig(id=os.environ.get("ARK_E2E_MODEL_ID", "doubao-seed-1-6-250615")),
            multiagent=MultiagentConfig(
                type="multiagent_20261001",
                subagents=MultiagentSubagentsConfig(
                    type="enabled",
                    predefined_agents=[AgentRef(type="self")],
                ),
            ),
        )
        assert created.multiagent is not None
        assert created.multiagent.subagents is not None

        fetched = client.agents.retrieve(created.id)
        assert fetched.id == created.id

        updated = client.agents.update(
            created.id,
            version=created.version,
            multiagent=MultiagentPatch(
                type="multiagent_20261001",
                subagents=MultiagentSubagentsConfig(
                    type="enabled",
                    predefined_agents=[],
                ),
            ),
        )
        assert updated.version > created.version

        listed = client.agents.list(limit=100)
        assert any(item.id == created.id for item in listed.data)

        legacy_headers = {"User-Agent": "ark-runtime-python/0.11.0"}
        with pytest.raises(Exception, match="MULTIAGENT_UNSUPPORTED_BY_CLIENT"):
            client.agents.retrieve(created.id, extra_headers=legacy_headers)
        with pytest.raises(Exception, match="MULTIAGENT_UNSUPPORTED_BY_CLIENT"):
            client.agents.update(
                created.id,
                version=updated.version,
                description="must be rejected",
                extra_headers=legacy_headers,
            )

        legacy_list = client.agents.list(limit=100, extra_headers=legacy_headers)
        legacy_item = next(item for item in legacy_list.data if item.id == created.id)
        assert legacy_item.multiagent is None
    finally:
        if created is not None:
            client.agents.delete(created.id)
