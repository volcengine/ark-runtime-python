# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
"""Self-hosted worker with client-side MCP tools.

Required::

    export ARK_API_KEY=...
    export MA_ENVIRONMENT_ID=env_xxx

Run the bundled MCP server from the repository root::

    python examples/self_hosted_mcp_worker/main.py -- \
        python examples/self_hosted_mcp_worker/server.py
"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
from typing import Dict, List, Optional

import anyio
from anyio.from_thread import BlockingPortal
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

from arkruntime import Ark
from arkruntime.mcp import custom_tool_items, mcp_tools
from arkruntime.selfhosted import ClientAPI, EnvironmentWorker, EnvironmentWorkerOptions


def required_env(name: str) -> str:
    """Return a required environment variable."""

    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def mcp_command_args(args: List[str]) -> List[str]:
    """Remove the optional argument separator from an MCP command."""

    return args[1:] if args and args[0] == "--" else args


def environment_without(name: str) -> Dict[str, str]:
    """Copy the process environment without a worker credential."""

    return {key: value for key, value in os.environ.items() if key != name}


async def list_all_tools(session: ClientSession) -> List[types.Tool]:
    """Return every page from the MCP tools/list endpoint."""

    tools: List[types.Tool] = []
    cursor: Optional[str] = None
    while True:
        params = types.PaginatedRequestParams(cursor=cursor) if cursor else None
        page = await session.list_tools(params=params)
        tools.extend(page.tools)
        cursor = page.next_cursor
        if not cursor:
            return tools


async def run() -> None:
    """Connect to MCP and run the self-hosted worker."""

    api_key = required_env("ARK_API_KEY")
    environment_id = required_env("MA_ENVIRONMENT_ID")
    command = mcp_command_args(sys.argv[1:])
    if not command:
        raise RuntimeError(
            "MCP server command is required; example: "
            "python examples/self_hosted_mcp_worker/main.py -- "
            "python examples/self_hosted_mcp_worker/server.py"
        )

    server = StdioServerParameters(
        command=command[0],
        args=command[1:],
        env=environment_without("ARK_API_KEY"),
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()
            tools = await list_all_tools(mcp_session)
            for declaration in custom_tool_items(tools):
                print(
                    "Agent custom tool: "
                    + json.dumps(declaration.to_dict(), ensure_ascii=False, separators=(",", ":")),
                    flush=True,
                )

            async with BlockingPortal() as portal:
                options = {"api_key": api_key}
                base_url = os.environ.get("ARK_BASE_URL", "")
                if base_url:
                    options["base_url"] = base_url
                client = Ark(**options)
                worker = EnvironmentWorker(
                    ClientAPI(client),
                    EnvironmentWorkerOptions(
                        environment_id=environment_id,
                        workdir=".",
                        custom_tools=mcp_tools(tools, mcp_session, portal=portal),
                    ),
                )
                previous_handlers = {
                    sig: signal.signal(sig, lambda _signum, _frame: worker.close())
                    for sig in (signal.SIGINT, signal.SIGTERM)
                }
                try:
                    await anyio.to_thread.run_sync(worker.run)
                finally:
                    worker.close()
                    client.close()
                    for sig, handler in previous_handlers.items():
                        signal.signal(sig, handler)


def main() -> None:
    """Run the example with the default AnyIO backend."""

    logging.basicConfig(level=logging.INFO)
    anyio.run(run)


if __name__ == "__main__":
    main()
