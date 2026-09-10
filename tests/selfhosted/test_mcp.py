# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict

import pytest

from arkruntime.selfhosted.mcp import (
    MCPCallToolResult,
    MCPContent,
    MCPResource,
    MCPToolDefinition,
    convert_call_tool_result,
    custom_tool_item,
    custom_tool_items,
    mcp_tool,
)
from arkruntime.selfhosted.tools import ToolContext
from arkruntime.selfhosted.types import ContentBlock


def test_custom_tool_item_adapts_schema_to_current_agent_contract() -> None:
    item = custom_tool_item(
        MCPToolDefinition(
            name="lookup_order",
            description="Lookup an order",
            input_schema={
                "type": "object",
                "properties": {"order_id": {"$ref": "#/$defs/order_id"}},
                "required": ["order_id"],
                "additionalProperties": False,
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$defs": {"order_id": {"type": "string", "minLength": 1}},
            },
        )
    )
    assert item.type == "custom"
    assert item.name == "lookup_order"
    assert item.description is not None
    assert item.description.startswith("Lookup an order")
    assert '"additionalProperties":false' in item.description
    assert '"$defs"' not in item.description
    assert '"$schema"' not in item.description
    assert item.input_schema is not None
    schema = item.input_schema.to_dict()
    assert set(schema) == {"type", "properties", "required"}
    assert schema["properties"] == {"order_id": {"type": "string", "minLength": 1}}


def test_custom_tool_item_retains_referenced_definitions() -> None:
    item = custom_tool_item(
        MCPToolDefinition(
            name="lookup",
            input_schema={
                "type": "object",
                "allOf": [{"$ref": "#/$defs/constraint"}],
                "$defs": {"constraint": {"additionalProperties": False}},
            },
        )
    )
    assert item.description is not None
    assert '"$defs"' in item.description
    assert '"$ref":"#/$defs/constraint"' in item.description


def test_custom_tool_item_describes_unresolved_references() -> None:
    item = custom_tool_item(
        MCPToolDefinition(
            name="lookup",
            input_schema={
                "type": "object",
                "properties": {"order": {"$ref": "https://example.com/order.json"}},
            },
        )
    )
    assert item.description is not None
    assert '"$ref":"https://example.com/order.json"' in item.description
    assert item.input_schema is not None
    assert item.input_schema.properties == {"order": {}}


def test_custom_tool_item_rejects_oversized_compatibility_description() -> None:
    with pytest.raises(ValueError, match="description exceeds"):
        custom_tool_item(
            MCPToolDefinition(
                name="large",
                description="a" * 10_000,
                input_schema={"type": "object", "additionalProperties": False},
            )
        )


@pytest.mark.parametrize("input_schema", [False, [], ""])
def test_custom_tool_item_rejects_falsy_non_object_schema(input_schema: Any) -> None:
    with pytest.raises(ValueError, match="input schema must be an object"):
        custom_tool_item(MCPToolDefinition(name="invalid", input_schema=input_schema))


def test_custom_tool_items_reject_duplicate_names() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        custom_tool_items([MCPToolDefinition(name="same"), MCPToolDefinition(name="same")])


def test_mcp_tool_calls_generic_client() -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.name = ""
            self.arguments: Dict[str, Any] = {}

        def call_tool(
            self,
            name: str,
            arguments: Dict[str, Any],
            context: ToolContext,
        ) -> MCPCallToolResult:
            self.name = name
            self.arguments = arguments
            return MCPCallToolResult(content=[MCPContent(type="text", text="echo: hello")])

    client = FakeClient()
    wrapped = mcp_tool(MCPToolDefinition(name="echo"), client)
    result = wrapped.execute({"text": "hello"}, ToolContext(workdir="."))
    assert not result.is_error
    assert [block.text for block in result.content] == ["echo: hello"]
    assert client.name == "echo"
    assert client.arguments == {"text": "hello"}


def test_convert_rich_content_through_tool() -> None:
    class FakeClient:
        def call_tool(
            self,
            name: str,
            arguments: Dict[str, Any],
            context: ToolContext,
        ) -> MCPCallToolResult:
            return MCPCallToolResult(
                content=[
                    MCPContent(type="image", mime_type="image/png", data="aW1hZ2U="),
                    MCPContent(
                        type="resource",
                        resource=MCPResource(
                            uri="file:///result.txt",
                            mime_type="text/plain",
                            text="resource text",
                        ),
                    ),
                ]
            )

    result = mcp_tool(MCPToolDefinition(name="rich"), FakeClient()).execute({}, ToolContext(workdir="."))
    blocks = list(result.content)
    assert not result.is_error
    assert blocks[0].source == {
        "type": "base64",
        "media_type": "image/png",
        "data": "aW1hZ2U=",
    }
    assert blocks[1].source == {
        "type": "text",
        "media_type": "text/plain",
        "data": "resource text",
    }


def test_unknown_content_rejects_the_entire_result() -> None:
    result = convert_call_tool_result(
        MCPCallToolResult(
            content=[
                MCPContent(type="text", text="kept"),
                MCPContent(type="future_audio"),
            ]
        )
    )
    assert result.is_error
    assert [block.text for block in result.content] == ["unsupported MCP content type future_audio"]


def test_text_resource_normalizes_mime_type() -> None:
    result = convert_call_tool_result(
        MCPCallToolResult(
            content=[
                MCPContent(
                    type="resource",
                    resource=MCPResource(mime_type="text/html", text="<p>hello</p>"),
                )
            ]
        )
    )
    assert not result.is_error
    assert list(result.content)[0].source == {
        "type": "text",
        "media_type": "text/plain",
        "data": "<p>hello</p>",
    }


def test_convert_empty_error_result_adds_message() -> None:
    class FakeClient:
        def call_tool(
            self,
            name: str,
            arguments: Dict[str, Any],
            context: ToolContext,
        ) -> MCPCallToolResult:
            return MCPCallToolResult(content=[], is_error=True)

    result = mcp_tool(MCPToolDefinition(name="failure"), FakeClient()).execute({}, ToolContext(workdir="."))
    assert result.is_error
    assert [block.text for block in result.content] == ["tool returned an error"]


def test_convert_error_does_not_expose_resource_uri() -> None:
    secret_uri = "https://example.com/file?signature=secret"

    class FakeClient:
        def call_tool(
            self,
            name: str,
            arguments: Dict[str, Any],
            context: ToolContext,
        ) -> MCPCallToolResult:
            return MCPCallToolResult(
                content=[
                    MCPContent(
                        type="resource",
                        resource=MCPResource(uri=secret_uri, mime_type="image/png"),
                    )
                ]
            )

    result = mcp_tool(MCPToolDefinition(name="resource"), FakeClient()).execute({}, ToolContext(workdir="."))
    assert result.is_error
    message = list(result.content)[0].text
    assert secret_uri not in message
    assert "secret" not in message


def test_empty_text_block_keeps_required_text_field() -> None:
    assert MCPContent(type="text", text="").text == ""
    assert ContentBlock(type="text", text="").to_dict() == {"type": "text", "text": ""}
