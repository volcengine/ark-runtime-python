# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
"""与具体 MCP SDK 无关的 self-hosted MCP 工具适配能力。"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple, Union

from typing_extensions import Protocol

from arkruntime.types.agent import CustomToolInputSchema, ToolItem

from .tools import Tool, ToolContext, ToolResult, error_result
from .types import ContentBlock

__all__ = [
    "MCPCallToolResult",
    "MCPClient",
    "MCPContent",
    "MCPResource",
    "MCPToolDefinition",
    "custom_tool_item",
    "custom_tool_items",
    "mcp_tool",
    "mcp_tools",
]

_SUPPORTED_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/gif", "image/webp"})
_COMPATIBILITY_DESCRIPTION_PREFIX = "\n\nMCP input constraints (JSON Schema): "
_MAX_CUSTOM_TOOL_DESCRIPTION_CHARS = 10_000
_IGNORED_TOP_LEVEL_SCHEMA_KEYWORDS = frozenset({"$anchor", "$comment", "$dynamicAnchor", "$id", "$schema", "title"})


@dataclass
class MCPToolDefinition:
    """MCP Tool 的协议无关描述。"""

    name: str
    description: str = ""
    input_schema: Any = None


@dataclass
class MCPResource:
    """MCP embedded resource 的协议无关表示。"""

    uri: str = ""
    mime_type: Optional[str] = None
    text: Optional[str] = None
    blob: Optional[Union[str, bytes]] = None


@dataclass
class MCPContent:
    """MCP Tool 返回的单个内容块。"""

    type: str
    text: Optional[str] = None
    mime_type: Optional[str] = None
    data: Optional[Union[str, bytes]] = None
    resource: Optional[MCPResource] = None


@dataclass
class MCPCallToolResult:
    """MCP Tool 调用结果的协议无关表示。"""

    content: Iterable[MCPContent]
    structured_content: Any = None
    is_error: bool = False


class MCPClient(Protocol):
    """self-hosted worker 调用 MCP Server 所需的最小接口。"""

    def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: ToolContext,
    ) -> Optional[MCPCallToolResult]:
        """调用一个 MCP Tool。"""


def custom_tool_item(tool: MCPToolDefinition) -> ToolItem:
    """把 MCP Tool 定义转换成 Agent ``type=custom`` 声明。"""

    if not tool.name:
        raise ValueError("mcp tool name is required")
    schema, constraints = _custom_tool_input_schema(tool.name, tool.input_schema)
    description = tool.description or tool.name
    if constraints:
        description += _COMPATIBILITY_DESCRIPTION_PREFIX + constraints
    if len(description) > _MAX_CUSTOM_TOOL_DESCRIPTION_CHARS:
        raise ValueError(
            f"mcp tool {tool.name} description exceeds "
            f"{_MAX_CUSTOM_TOOL_DESCRIPTION_CHARS} characters after adding input constraints"
        )
    return ToolItem(
        type="custom",
        name=tool.name,
        description=description,
        input_schema=schema,
    )


def _custom_tool_input_schema(tool_name: str, value: Any) -> Tuple[CustomToolInputSchema, str]:
    raw_schema = {"type": "object"} if value is None else value
    if not isinstance(raw_schema, Mapping):
        raise ValueError(f"mcp tool {tool_name} input schema must be an object")
    schema = dict(raw_schema)
    schema_type = schema.get("type", "object")
    if schema_type is None:
        schema_type = "object"
    if not isinstance(schema_type, str):
        raise ValueError(f"mcp tool {tool_name} input schema type must be a string")
    if schema_type != "object":
        raise ValueError(f"mcp tool {tool_name} input schema top-level type must be 'object'")
    properties = schema.get("properties")
    if properties is not None and not isinstance(properties, Mapping):
        raise ValueError(f"mcp tool {tool_name} input schema properties must be an object")
    required = schema.get("required")
    if required is not None and (not isinstance(required, list) or not all(isinstance(name, str) for name in required)):
        raise ValueError(f"mcp tool {tool_name} input schema required must be an array of strings")

    constraints = {
        key: item
        for key, item in schema.items()
        if key not in {"type", "properties", "required"} and key not in _IGNORED_TOP_LEVEL_SCHEMA_KEYWORDS
    }
    resolved_properties, unresolved = _resolve_schema_value(dict(properties or {}), schema, set())
    if unresolved:
        constraints["properties"] = properties
    _remove_unreferenced_definitions(constraints)

    fields: Dict[str, Any] = {"type": "object"}
    if properties is not None:
        fields["properties"] = resolved_properties
    if required is not None:
        fields["required"] = list(required)
    constraints_json = (
        json.dumps(constraints, ensure_ascii=False, separators=(",", ":"), sort_keys=True) if constraints else ""
    )
    return CustomToolInputSchema(**fields), constraints_json


def _remove_unreferenced_definitions(constraints: Dict[str, Any]) -> None:
    definition_references = {
        "$defs": "#/$defs",
        "definitions": "#/definitions",
    }
    for definition_key, reference_prefix in definition_references.items():
        if definition_key not in constraints:
            continue
        if not any(
            key != definition_key and _contains_reference(item, reference_prefix) for key, item in constraints.items()
        ):
            constraints.pop(definition_key)


def _contains_reference(value: Any, prefix: str) -> bool:
    if isinstance(value, Mapping):
        reference = value.get("$ref")
        if isinstance(reference, str) and (reference == prefix or reference.startswith(prefix + "/")):
            return True
        return any(_contains_reference(item, prefix) for item in value.values())
    if isinstance(value, list):
        return any(_contains_reference(item, prefix) for item in value)
    return False


def _resolve_schema_value(value: Any, root: Mapping[str, Any], resolving: Set[str]) -> Tuple[Any, bool]:
    if isinstance(value, Mapping):
        reference = value.get("$ref")
        if isinstance(reference, str):
            target = _resolve_json_pointer(root, reference)
            if target is not None and reference not in resolving:
                resolving.add(reference)
                resolved_target, unresolved = _resolve_schema_value(target, root, resolving)
                resolving.remove(reference)
                if isinstance(resolved_target, Mapping):
                    merged = dict(resolved_target)
                    merged.update({key: item for key, item in value.items() if key != "$ref"})
                    resolved, merged_unresolved = _resolve_schema_value(merged, root, resolving)
                    return resolved, unresolved or merged_unresolved
            return _map_without_reference(value, root, resolving)

        result: Dict[str, Any] = {}
        unresolved = False
        for key, item in value.items():
            result[key], item_unresolved = _resolve_schema_value(item, root, resolving)
            unresolved = unresolved or item_unresolved
        return result, unresolved
    if isinstance(value, list):
        result = []
        unresolved = False
        for item in value:
            resolved, item_unresolved = _resolve_schema_value(item, root, resolving)
            result.append(resolved)
            unresolved = unresolved or item_unresolved
        return result, unresolved
    return value, False


def _map_without_reference(
    value: Mapping[str, Any],
    root: Mapping[str, Any],
    resolving: Set[str],
) -> Tuple[Dict[str, Any], bool]:
    result: Dict[str, Any] = {}
    unresolved = True
    for key, item in value.items():
        if key == "$ref":
            continue
        result[key], item_unresolved = _resolve_schema_value(item, root, resolving)
        unresolved = unresolved or item_unresolved
    return result, unresolved


def _resolve_json_pointer(root: Mapping[str, Any], reference: str) -> Optional[Any]:
    if not reference.startswith("#/"):
        return None
    current: Any = root
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, Mapping) or token not in current:
            return None
        current = current[token]
    return current


def custom_tool_items(tools: Iterable[MCPToolDefinition]) -> List[ToolItem]:
    """批量生成 Agent custom tool 声明。"""

    result: List[ToolItem] = []
    seen = set()
    for tool in tools:
        if tool.name in seen:
            raise ValueError(f"duplicate mcp tool name {tool.name!r}")
        seen.add(tool.name)
        result.append(custom_tool_item(tool))
    return result


class _MCPTool(Tool):
    def __init__(self, tool: MCPToolDefinition, client: MCPClient) -> None:
        if not tool.name:
            raise ValueError("mcp tool name is required")
        self.name = tool.name
        self._client = client

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        if tool_input is None:
            arguments: Dict[str, Any] = {}
        elif isinstance(tool_input, Mapping):
            arguments = dict(tool_input)
        else:
            return error_result(f"mcp tool {self.name}: input must be an object")
        try:
            result = self._client.call_tool(self.name, arguments, context)
            return convert_call_tool_result(result)
        except Exception as exc:  # noqa: BLE001 - MCP failures are tool results.
            return error_result(f"mcp tool {self.name}: {exc}")


def mcp_tool(tool: MCPToolDefinition, client: MCPClient) -> Tool:
    """把 MCP Tool 定义包装成 worker Custom Tool。"""

    return _MCPTool(tool, client)


def mcp_tools(tools: Iterable[MCPToolDefinition], client: MCPClient) -> Dict[str, Tool]:
    """批量包装 MCP Tools。"""

    result: Dict[str, Tool] = {}
    for tool in tools:
        wrapped = mcp_tool(tool, client)
        if wrapped.name in result:
            raise ValueError(f"duplicate mcp tool name {wrapped.name!r}")
        result[wrapped.name] = wrapped
    return result


def convert_call_tool_result(result: Optional[MCPCallToolResult]) -> ToolResult:
    """把协议无关的 MCP 结果转换成 worker Tool Result。"""

    if result is None:
        return error_result("mcp tool returned no result")
    blocks: List[ContentBlock] = []
    for item in result.content:
        try:
            blocks.append(_content_block(item))
        except ValueError as exc:
            return error_result(str(exc))
    if not blocks and result.structured_content is not None:
        blocks.append(ContentBlock(type="text", text=json.dumps(result.structured_content, separators=(",", ":"))))
    if not blocks and result.is_error:
        blocks.append(ContentBlock(type="text", text="tool returned an error"))
    return ToolResult(blocks, is_error=bool(result.is_error))


def _content_block(content: MCPContent) -> ContentBlock:
    if content.type == "text":
        return ContentBlock(type="text", text=content.text or "")
    if content.type == "image":
        if content.mime_type not in _SUPPORTED_IMAGE_MIME_TYPES:
            raise ValueError(f"unsupported image MIME type {content.mime_type!r}")
        return _base64_block("image", content.mime_type, content.data)
    if content.type == "resource":
        return _resource_block(content.resource)
    raise ValueError(f"unsupported MCP content type {content.type}")


def _resource_block(resource: Optional[MCPResource]) -> ContentBlock:
    if resource is None:
        raise ValueError("embedded MCP resource has no content")
    mime_type = resource.mime_type
    if mime_type in _SUPPORTED_IMAGE_MIME_TYPES:
        if resource.blob is None:
            raise ValueError("image resource must contain blob data")
        return _base64_block("image", mime_type, resource.blob)
    if mime_type == "application/pdf":
        if resource.blob is None:
            raise ValueError("PDF resource must contain blob data")
        return _base64_block("document", mime_type, resource.blob)
    if mime_type is None or mime_type == "" or mime_type.startswith("text/"):
        text = resource.text
        if text is None and resource.blob is not None:
            raw = resource.blob if isinstance(resource.blob, bytes) else base64.b64decode(resource.blob)
            text = raw.decode("utf-8")
        return ContentBlock(
            type="document",
            source={"type": "text", "media_type": "text/plain", "data": text or ""},
        )
    raise ValueError(f"unsupported resource MIME type {mime_type!r}")


def _base64_block(block_type: str, mime_type: str, data: Optional[Union[str, bytes]]) -> ContentBlock:
    if data is None:
        encoded = ""
    elif isinstance(data, str):
        encoded = data
    else:
        encoded = base64.b64encode(data).decode("ascii")
    return ContentBlock(
        type=block_type,
        source={"type": "base64", "media_type": mime_type, "data": encoded},
    )
