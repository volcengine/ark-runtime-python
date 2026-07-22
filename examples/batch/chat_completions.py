"""Batch chat completions: parallel synchronous online inference.

Uses the per-model breaker + retry loop on /batch/chat/completions.
Streaming is not supported on this path.
"""

from __future__ import annotations

import queue
import sys
from datetime import datetime
from multiprocessing.pool import ThreadPool

from arkruntime import Ark


def worker(worker_id: int, client: Ark, requests: "queue.Queue[dict | None]") -> None:
    print(f"Worker {worker_id} is starting.")

    while True:
        request = requests.get()

        # check for signal of no more request
        if not request:
            # put back on the queue for other workers
            requests.put(request)
            return

        try:
            completion = client.batch.chat.completions.create(**request)
            print(completion)
        except Exception as e:
            print(e, file=sys.stderr)
        finally:
            requests.task_done()


def main() -> None:
    start = datetime.now()
    max_concurrent_tasks, task_num = 10, 100

    requests: "queue.Queue[dict | None]" = queue.Queue()
    client = Ark(timeout=24 * 3600)

    # mock `task_num` tasks
    for _ in range(task_num):
        requests.put(
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

    # signal no more requests
    requests.put(None)

    with ThreadPool(max_concurrent_tasks) as pool:
        for i in range(max_concurrent_tasks):
            pool.apply_async(worker, args=(i, client, requests))

        pool.close()
        pool.join()

    client.close()

    end = datetime.now()
    print(f"Total time: {end - start}, Total task: {task_num}")


if __name__ == "__main__":
    main()
