# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
"""把官方 MCP Python SDK 适配到方舟 self-hosted MCP 接口。

安装可选依赖：``pip install 'arkruntime[mcp]'``。官方 MCP 包需要
Python 3.10 或更高版本。调用方应在 AnyIO 事件循环中创建
``BlockingPortal``，并保证 portal 与 MCP ``ClientSession`` 的生命周期覆盖 worker。
"""

from __future__ import annotations

import concurrent.futures
import contextlib
import time
from typing import Any, Dict, Iterable, List, Optional

try:
    from anyio.from_thread import BlockingPortal
    from mcp import ClientSession, types
except ImportError as exc:  # pragma: no cover - depends on the optional extra.
    raise ImportError(
        "The 'mcp' package is required for MCP helpers. Install it with: "
        "pip install 'arkruntime[mcp]'. Python 3.10 or newer is required."
    ) from exc

from arkruntime.selfhosted.mcp import (
    MCPCallToolResult,
    MCPClient,
    MCPContent,
    MCPResource,
    MCPToolDefinition,
)
from arkruntime.selfhosted.mcp import (
    custom_tool_item as core_custom_tool_item,
)
from arkruntime.selfhosted.mcp import (
    custom_tool_items as core_custom_tool_items,
)
from arkruntime.selfhosted.mcp import (
    mcp_tool as core_mcp_tool,
)
from arkruntime.selfhosted.mcp import (
    mcp_tools as core_mcp_tools,
)
from arkruntime.selfhosted.tools import Tool, ToolContext
from arkruntime.types.agent import ToolItem

__all__ = ["AnyIOMCPClient", "custom_tool_item", "custom_tool_items", "mcp_tool", "mcp_tools"]

_MISSING = object()


def _field(value: Any, snake_name: str, camel_name: str, default: Any = _MISSING) -> Any:
    if hasattr(value, snake_name):
        return getattr(value, snake_name)
    if hasattr(value, camel_name):
        return getattr(value, camel_name)
    if default is not _MISSING:
        return default
    raise AttributeError(snake_name)


class AnyIOMCPClient(MCPClient):
    """通过 AnyIO portal 从 worker 线程调用异步 MCP ClientSession。"""

    def __init__(
        self,
        client: ClientSession,
        portal: BlockingPortal,
        *,
        timeout: Optional[float] = None,
        poll_interval: float = 0.25,
    ) -> None:
        if client is None:
            raise ValueError("mcp client is required")
        if portal is None:
            raise ValueError("anyio blocking portal is required")
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive")
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self._client = client
        self._portal = portal
        self._timeout = timeout
        self._poll_interval = poll_interval

    def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: ToolContext,
    ) -> Optional[MCPCallToolResult]:
        future = self._portal.start_task_soon(self._client.call_tool, name, arguments)
        started = time.monotonic()
        while True:
            try:
                return _call_tool_result(future.result(timeout=self._poll_interval))
            except concurrent.futures.TimeoutError:
                if _is_cancelled(context):
                    _cancel_and_wait(future)
                    raise RuntimeError("execution canceled")
                if self._timeout is not None and time.monotonic() - started >= self._timeout:
                    _cancel_and_wait(future)
                    raise RuntimeError(f"execution timed out after {self._timeout:g} seconds")


def custom_tool_item(tool: "types.Tool") -> ToolItem:
    """把官方 MCP Tool 转换成 Agent custom tool 声明。"""

    return core_custom_tool_item(_tool_definition(tool))


def custom_tool_items(tools: Iterable["types.Tool"]) -> List[ToolItem]:
    """批量转换官方 MCP Tools。"""

    return core_custom_tool_items([_tool_definition(tool) for tool in tools])


def mcp_tool(
    tool: "types.Tool",
    client: ClientSession,
    *,
    portal: BlockingPortal,
    timeout: Optional[float] = None,
) -> Tool:
    """把官方 MCP Tool 包装成 worker Custom Tool。"""

    return core_mcp_tool(_tool_definition(tool), AnyIOMCPClient(client, portal, timeout=timeout))


def mcp_tools(
    tools: Iterable["types.Tool"],
    client: ClientSession,
    *,
    portal: BlockingPortal,
    timeout: Optional[float] = None,
) -> Dict[str, Tool]:
    """批量包装官方 MCP Tools。"""

    return core_mcp_tools(
        [_tool_definition(tool) for tool in tools],
        AnyIOMCPClient(client, portal, timeout=timeout),
    )


def _tool_definition(tool: "types.Tool") -> MCPToolDefinition:
    if tool is None:
        raise ValueError("mcp tool is required")
    return MCPToolDefinition(
        name=tool.name,
        description=tool.description or "",
        input_schema=_field(tool, "input_schema", "inputSchema", {"type": "object"}),
    )


def _call_tool_result(result: "types.CallToolResult") -> Optional[MCPCallToolResult]:
    if result is None:
        return None
    return MCPCallToolResult(
        content=[_content(item) for item in result.content],
        structured_content=_field(result, "structured_content", "structuredContent", None),
        is_error=bool(_field(result, "is_error", "isError", False)),
    )


def _content(content: "types.ContentBlock") -> MCPContent:
    if isinstance(content, types.TextContent):
        return MCPContent(type="text", text=content.text)
    if isinstance(content, types.ImageContent):
        return MCPContent(
            type="image",
            mime_type=_field(content, "mime_type", "mimeType"),
            data=content.data,
        )
    if isinstance(content, types.EmbeddedResource):
        return MCPContent(type="resource", resource=_resource(content.resource))
    return MCPContent(type=str(getattr(content, "type", type(content).__name__)))


def _resource(resource: Any) -> MCPResource:
    return MCPResource(
        uri=str(resource.uri),
        mime_type=_field(resource, "mime_type", "mimeType", None),
        text=getattr(resource, "text", None),
        blob=getattr(resource, "blob", None),
    )


def _is_cancelled(context: ToolContext) -> bool:
    cancel_event = context.cancel_event
    return cancel_event is not None and bool(getattr(cancel_event, "is_set", lambda: False)())


def _cancel_and_wait(future: "concurrent.futures.Future[Any]") -> None:
    future.cancel()
    with contextlib.suppress(concurrent.futures.CancelledError, concurrent.futures.TimeoutError):
        future.result(timeout=1)
