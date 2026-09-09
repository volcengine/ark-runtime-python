# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

import threading
from typing import Any

import anyio
import pytest

pytest.importorskip("mcp")

from mcp import types  # noqa: E402

from arkruntime.mcp import AnyIOMCPClient, custom_tool_item, mcp_tool  # noqa: E402
from arkruntime.selfhosted.tools import ToolContext  # noqa: E402


def test_custom_tool_item_adapts_schema_to_current_agent_contract() -> None:
    item = custom_tool_item(
        types.Tool(
            name="lookup_order",
            inputSchema={
                "type": "object",
                "properties": {"order_id": {"$ref": "#/$defs/order_id"}},
                "required": ["order_id"],
                "additionalProperties": False,
                "$defs": {"order_id": {"type": "string"}},
            },
        )
    )
    schema = item.input_schema.to_dict()
    assert set(schema) == {"type", "properties", "required"}
    assert schema["properties"] == {"order_id": {"type": "string"}}
    assert item.description is not None
    assert '"additionalProperties":false' in item.description
    assert '"$defs"' not in item.description


@pytest.mark.parametrize("backend", ["asyncio", "trio"])
def test_mcp_tool_uses_anyio_portal(backend: str) -> None:
    async def run() -> None:
        class FakeClient:
            async def call_tool(self, name: str, arguments: dict) -> types.CallToolResult:
                assert name == "echo"
                assert arguments == {"text": "hello"}
                return types.CallToolResult(content=[types.TextContent(type="text", text="echo: hello")])

        async with anyio.from_thread.BlockingPortal() as portal:
            wrapped = mcp_tool(
                types.Tool(name="echo", inputSchema={"type": "object"}),
                FakeClient(),  # type: ignore[arg-type]
                portal=portal,
            )
            result = await anyio.to_thread.run_sync(
                wrapped.execute,
                {"text": "hello"},
                ToolContext(workdir="."),
            )
            assert not result.is_error
            assert [block.text for block in result.content] == ["echo: hello"]

    anyio.run(run, backend=backend)


def test_adapter_handles_v1_result_without_structured_content() -> None:
    class V1Result:
        content = [types.TextContent(type="text", text="ok")]
        isError = False

    class Portal:
        def start_task_soon(self, func: Any, *args: Any) -> Any:
            class Future:
                def result(self, timeout: float) -> Any:
                    return V1Result()

            return Future()

    class Client:
        async def call_tool(self, name: str, arguments: dict) -> Any:
            return V1Result()

    wrapped = mcp_tool(
        types.Tool(name="v1", inputSchema={"type": "object"}),
        Client(),  # type: ignore[arg-type]
        portal=Portal(),  # type: ignore[arg-type]
    )
    result = wrapped.execute({}, ToolContext(workdir="."))
    assert not result.is_error
    assert [block.text for block in result.content] == ["ok"]


@pytest.mark.parametrize("backend", ["asyncio", "trio"])
def test_mcp_tool_cancellation_stops_async_task(backend: str) -> None:
    async def run() -> None:
        cancel_event = threading.Event()
        task_stopped = anyio.Event()

        class SlowClient:
            async def call_tool(self, name: str, arguments: dict) -> types.CallToolResult:
                try:
                    await anyio.sleep_forever()
                finally:
                    task_stopped.set()

        async def cancel() -> None:
            await anyio.sleep(0.05)
            cancel_event.set()

        async with anyio.from_thread.BlockingPortal() as portal:
            wrapped = mcp_tool(
                types.Tool(name="slow", inputSchema={"type": "object"}),
                SlowClient(),  # type: ignore[arg-type]
                portal=portal,
            )
            async with anyio.create_task_group() as task_group:
                task_group.start_soon(cancel)
                result = await anyio.to_thread.run_sync(
                    wrapped.execute,
                    {},
                    ToolContext(workdir=".", cancel_event=cancel_event),
                )
            assert result.is_error
            assert "execution canceled" in (list(result.content)[0].text or "")
            with anyio.fail_after(1):
                await task_stopped.wait()

    anyio.run(run, backend=backend)


def test_mcp_client_timeout_stops_async_task() -> None:
    async def run() -> None:
        task_stopped = anyio.Event()

        class SlowClient:
            async def call_tool(self, name: str, arguments: dict) -> types.CallToolResult:
                try:
                    await anyio.sleep_forever()
                finally:
                    task_stopped.set()

        async with anyio.from_thread.BlockingPortal() as portal:
            client = AnyIOMCPClient(
                SlowClient(),  # type: ignore[arg-type]
                portal,
                timeout=0.05,
                poll_interval=0.01,
            )
            with pytest.raises(RuntimeError, match="timed out"):
                await anyio.to_thread.run_sync(
                    client.call_tool,
                    "slow",
                    {},
                    ToolContext(workdir="."),
                )
            with anyio.fail_after(1):
                await task_stopped.wait()

    anyio.run(run)
