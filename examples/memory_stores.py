"""MemoryStore + Memory lifecycle example.

A MemoryStore is a namespace of Memory documents keyed by path. Covers the
full CRUD on both levels:

    POST   /api/v3/memory_stores                        (client.memory_stores.create)
    GET    /api/v3/memory_stores/:store_id              (client.memory_stores.retrieve)
    GET    /api/v3/memory_stores                        (client.memory_stores.list)
    POST   /api/v3/memory_stores/:store_id              (client.memory_stores.update)
    POST   /api/v3/memory_stores/:store_id/memories     (client.memory_stores.memories.create)
    GET    /api/v3/memory_stores/:store_id/memories/:id (client.memory_stores.memories.retrieve)
    GET    /api/v3/memory_stores/:store_id/memories     (client.memory_stores.memories.list)
    POST   /api/v3/memory_stores/:store_id/memories/:id (client.memory_stores.memories.update)
    DELETE /api/v3/memory_stores/:store_id/memories/:id (client.memory_stores.memories.delete)
    DELETE /api/v3/memory_stores/:store_id              (client.memory_stores.delete)

    export ARK_API_KEY=...
    python examples/memory_stores.py
"""

from __future__ import annotations

import os
import time

from arkruntime import Ark


def main() -> None:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        raise SystemExit("set ARK_API_KEY")

    client = Ark(api_key=api_key)

    # 1. Create a memory store.
    store = client.memory_stores.create(name=f"example-store-{time.time_ns()}")
    print(f"store:      id={store.id} name={store.name}")

    mem = None
    try:
        # 2. Create a memory doc inside it.
        path = f"/example/note-{time.time_ns()}.md"
        mem = client.memory_stores.memories.create(
            store.id,
            path=path,
            content="hello from ark-runtime-python example",
        )
        print(f"memory:     id={mem.id} path={mem.path} sha256={mem.content_sha256}")

        # 3. Get + list.
        got = client.memory_stores.memories.retrieve(store.id, mem.id)
        print(f"get:        id={got.id} path={got.path}")

        listed = client.memory_stores.memories.list(store.id, limit=10)
        print(f"list:       {len(listed.data)} items in store")

        # 4. Update — the SHA256 should change after new content.
        client.memory_stores.memories.update(store.id, mem.id, content="updated content")
        got2 = client.memory_stores.memories.retrieve(store.id, mem.id)
        print(f"updated:    id={got2.id} new_sha256={got2.content_sha256} (was {mem.content_sha256})")

        # 5. Delete the memory (store is cleaned up in `finally`).
        client.memory_stores.memories.delete(store.id, mem.id)
        print(f"memory:     deleted id={mem.id}")
    finally:
        client.memory_stores.delete(store.id)
        print(f"store:      deleted id={store.id}")


if __name__ == "__main__":
    main()
