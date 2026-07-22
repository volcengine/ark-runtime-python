"""Async batch chat completions: parallel synchronous online inference."""

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
            completion = await client.batch.chat.completions.create(**request)
            print(completion)
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
                "messages": [
                    {
                        "role": "system",
                        "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手",
                    },
                    {"role": "user", "content": "常见的十字花科植物有哪些？"},
                ],
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
