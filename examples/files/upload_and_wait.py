"""Upload a local file, wait for processing, then list and delete."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from arkruntime import Ark


def main() -> None:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        sys.exit("set ARK_API_KEY")

    client = Ark(api_key=api_key)
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__)

    print(f"uploading {target}")
    file = client.files.create(file=target, purpose="user_data")
    print(f"  -> id={file.id} status={file.status}")

    file = client.files.wait_for_processing(file.id)
    print(f"  ready: status={file.status} bytes={file.bytes} mime={file.mime_type}")

    page = client.files.list(limit=5, order="desc")
    for f in page.data:
        print(f"  {f.id}\t{f.created_at}\t{f.filename}")

    deleted = client.files.delete(file.id)
    print(f"deleted: {deleted.id} ({deleted.deleted})")


if __name__ == "__main__":
    main()
