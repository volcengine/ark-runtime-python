# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
"""Minimal stdio MCP server used by the self-hosted MCP worker example."""

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:  # MCP Python SDK 1.x.
    from mcp.server.fastmcp import FastMCP as MCPServer

server = MCPServer("ark-self-hosted-mcp-example")


@server.tool(name="mcp_echo", description="Echo text through the local MCP server.")
def mcp_echo(text: str) -> str:
    """Echo text through the local MCP server."""

    return "MCP echo: " + text


if __name__ == "__main__":
    server.run(transport="stdio")
