"""Async batch embeddings: parallel synchronous calls to /batch/embeddings."""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime

from arkruntime import AsyncArk


async def worker(worker_id: int, client: AsyncArk, requests: "asyncio.Queue[dict]") -> None:
    print(f"Worker {worker_id} is starting.")

    while True:
        request = await requests.get()
        try:
            resp = await client.batch.embeddings.create(**request)
            print(resp)
        except Exception as e:
            print(e, file=sys.stderr)
        finally:
            requests.task_done()


async def main() -> None:
    start = datetime.now()
    max_concurrent_tasks, task_num = 10, 100

    requests: "asyncio.Queue[dict]" = asyncio.Queue()
    client = AsyncArk(timeout=24 * 3600)

    for _ in range(task_num):
        await requests.put(
            {
                "model": "${YOUR_ENDPOINT_ID}",
                "input": ["花椰菜又称菜花、花菜，是一种常见的蔬菜。"],
            }
        )

    tasks = [asyncio.create_task(worker(i, client, requests)) for i in range(max_concurrent_tasks)]

    await requests.join()

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    await client.close()

    end = datetime.now()
    print(f"Total time: {end - start}, Total task: {task_num}")


if __name__ == "__main__":
    asyncio.run(main())
