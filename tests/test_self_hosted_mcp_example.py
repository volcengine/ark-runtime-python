# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional

import anyio
import pytest

pytest.importorskip("mcp")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def load_example_list_all_tools() -> Any:
    example_path = Path(__file__).parents[1] / "examples" / "self_hosted_mcp_worker" / "main.py"
    spec = importlib.util.spec_from_file_location("self_hosted_mcp_worker_example", example_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.list_all_tools


def test_list_all_tools_follows_pagination_cursor() -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.cursors: List[Optional[str]] = []

        async def list_tools(self, *, params: Any = None) -> Any:
            cursor = params.cursor if params is not None else None
            self.cursors.append(cursor)
            if cursor is None:
                return SimpleNamespace(tools=["first"], next_cursor="page-2")
            return SimpleNamespace(tools=["second"], next_cursor=None)

    async def run() -> None:
        session = FakeSession()
        tools = await load_example_list_all_tools()(session)
        assert tools == ["first", "second"]
        assert session.cursors == [None, "page-2"]

    anyio.run(run)


def test_bundled_mcp_server_lists_and_executes_echo_tool() -> None:
    async def run() -> None:
        server_path = Path(__file__).parents[1] / "examples" / "self_hosted_mcp_worker" / "server.py"
        server = StdioServerParameters(command=sys.executable, args=[str(server_path)])
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert [tool.name for tool in listed.tools] == ["mcp_echo"]
                result = await session.call_tool("mcp_echo", {"text": "hello"})
                assert not getattr(result, "is_error", getattr(result, "isError", False))
                assert result.content[0].text == "MCP echo: hello"

    anyio.run(run)
