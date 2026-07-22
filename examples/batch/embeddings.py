"""Batch embeddings: parallel synchronous calls to /batch/embeddings."""

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
        if not request:
            requests.put(request)
            return

        try:
            resp = client.batch.embeddings.create(**request)
            print(resp)
        except Exception as e:
            print(e, file=sys.stderr)
        finally:
            requests.task_done()


def main() -> None:
    start = datetime.now()
    max_concurrent_tasks, task_num = 10, 100

    requests: "queue.Queue[dict | None]" = queue.Queue()
    client = Ark(timeout=24 * 3600)

    for _ in range(task_num):
        requests.put(
            {
                "model": "${YOUR_ENDPOINT_ID}",
                "input": ["花椰菜又称菜花、花菜，是一种常见的蔬菜。"],
            }
        )

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
