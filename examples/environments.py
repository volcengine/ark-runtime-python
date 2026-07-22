"""Environment lifecycle example — Create/Get/List/Update/Delete.

An Environment is the sandbox (network + filesystem policy) an Agent runs
inside during a Session. This example uses the cloud environment with
unrestricted networking; production usage will typically restrict either.

    export ARK_API_KEY=...
    python examples/environments.py
"""

from __future__ import annotations

import os
import time

from arkruntime import Ark
from arkruntime.types.environment.env_config import EnvConfig
from arkruntime.types.environment.networking_config import NetworkingConfig


def main() -> None:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise SystemExit("set ARK_API_KEY")

    client = Ark(api_key=api_key)

    # 1. Create — cloud + unrestricted network.
    name = f"example-env-{time.time_ns()}"
    created = client.environments.create(
        name=name,
        config=EnvConfig(
            type="cloud",
            networking=NetworkingConfig(type="unrestricted"),
        ),
    )
    print(f"created:    id={created.id} name={created.name}")

    try:
        # 2. Get
        got = client.environments.retrieve(created.id)
        print(f"get:        id={got.id} name={got.name} type={got.type}")

        # 3. List
        listed = client.environments.list(limit=5)
        print(f"list:       {len(listed.data)} items, next_page={listed.next_page!r}")

        # 4. Update — attach a description.
        updated = client.environments.update(
            created.id,
            description="updated by ark-runtime-python example",
        )
        print(f"updated:    id={updated.id} description={updated.description!r}")
    finally:
        # 5. Delete
        deleted = client.environments.delete(created.id)
        print(f"deleted:    id={deleted.id} deleted={deleted.deleted}")


if __name__ == "__main__":
    main()
