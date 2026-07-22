"""Agent lifecycle example — Create/Get/List/Update/ListVersions/Delete.

Runs against the outward /api/v3/agents endpoint.

    export ARK_API_KEY=...
    export ARK_MODEL_ID=doubao-seed-1-8-251228   # or whatever you have access to
    python examples/agents.py
"""

from __future__ import annotations

import os
import time

from arkruntime import Ark
from arkruntime.types.agent.model_config import ModelConfig


def main() -> None:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise SystemExit("set ARK_API_KEY")
    model_id = os.environ.get("ARK_MODEL_ID", "${YOUR_MODEL_ID}")

    client = Ark(api_key=api_key)

    # 1. Create
    name = f"example-agent-{time.time_ns()}"
    created = client.agents.create(
        name=name,
        model=ModelConfig(id=model_id),
        description="created by ark-runtime-python example",
    )
    print(f"created:    id={created.id} version={created.version} name={created.name}")

    try:
        # 2. Get
        got = client.agents.retrieve(created.id)
        print(f"get:        id={got.id} name={got.name}")

        # 3. List — takes limit / page / created_at_gte / created_at_lte.
        listed = client.agents.list(limit=5)
        print(f"list:       {len(listed.data)} items, next_page={listed.next_page!r}")

        # 4. Update — bumps version. Requires the previous version for optimistic
        #    concurrency control.
        updated = client.agents.update(
            created.id,
            version=created.version,
            description="updated by ark-runtime-python example",
        )
        print(f"updated:    id={updated.id} version={updated.version} (was {created.version})")

        # 5. List versions — should see at least v1 (create) + v2 (update).
        versions = client.agents.list_versions(created.id, limit=10)
        print(f"versions:   {len(versions.data)} items")
    finally:
        # 6. Delete
        deleted = client.agents.delete(created.id)
        print(f"deleted:    id={deleted.id} deleted={deleted.deleted}")


if __name__ == "__main__":
    main()
