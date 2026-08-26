# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

# Prepare the Python environment from the repository root before running:
#
#   python3 -m venv .venv
#   source .venv/bin/activate
#
#   python -m pip install -U pip
#   python -m pip install -e .
#   python examples/self_hosted_worker.py

from __future__ import annotations

import logging
import os
import signal
import sys

_SETUP_INSTRUCTIONS = """Run these commands from the repository root:

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e .
python examples/self_hosted_worker.py"""

try:
    from arkruntime import Ark
    from arkruntime.selfhosted import ClientAPI, EnvironmentWorker, EnvironmentWorkerOptions
except ModuleNotFoundError as exc:
    print(f"failed to import arkruntime: {exc}", file=sys.stderr)
    print(_SETUP_INSTRUCTIONS, file=sys.stderr)
    raise SystemExit(1) from exc

logger = logging.getLogger("arkruntime.selfhosted.example")


def configure_logging() -> None:
    level_name = os.environ.get("ARK_LOG", "info").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


def required_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> None:
    configure_logging()
    base_url = os.environ.get("ARK_BASE_URL", "")
    environment_id = required_env("MA_ENVIRONMENT_ID")
    options = EnvironmentWorkerOptions(
        environment_id=environment_id,
        worker_id=os.environ.get("MA_WORKER_ID", ""),
        workdir=os.environ.get("MA_WORKDIR", "."),
    )
    client_options = {"api_key": required_env("ARK_API_KEY")}
    if base_url:
        client_options["base_url"] = base_url
    client = Ark(**client_options)
    worker = EnvironmentWorker(ClientAPI(client), options)
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda _signum, _frame: worker.close())
    logger.info(
        "starting self-hosted worker base_url=%s environment_id=%s worker_id=%s workdir=%s",
        base_url or "default",
        environment_id,
        options.worker_id,
        options.workdir,
    )
    try:
        worker.run()
    finally:
        worker.close()
        client.close()


if __name__ == "__main__":
    main()
