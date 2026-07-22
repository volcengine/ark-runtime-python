# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

"""Parsed Responses-API sibling models.

Adapted from an upstream SDK ``types/responses/parsed_response.py``
to the ark-apis-generated type names:

  upstream                     -> ark-apis
  ResponseOutputText           -> OutputContentItemText
  ResponseOutputMessage        -> ItemOutputMessage
  ResponseFunctionToolCall     -> ItemFunctionToolCall
  Response                     -> Response

The ark-apis Responses API does not expose a refusal content type, so
``ParsedContent`` is just the parsed-text variant rather than a union.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Generic, Optional, TypeVar
from typing_extensions import TypeAlias

from arkruntime._models import GenericModel
from .response import Response
from .item_output_message import ItemOutputMessage
from .output_content_item_text import OutputContentItemText
from .item_function_tool_call import ItemFunctionToolCall

__all__ = [
    "ParsedContent",
    "ParsedResponse",
    "ParsedResponseOutputItem",
    "ParsedResponseOutputMessage",
    "ParsedResponseOutputText",
    "ParsedResponseFunctionToolCall",
]

ContentType = TypeVar("ContentType")

# pyright: reportIncompatibleVariableOverride=false


class ParsedResponseOutputText(
    OutputContentItemText, GenericModel, Generic[ContentType]
):
    """``output_text`` content item augmented with a typed ``parsed`` slot
    populated when the caller provided a ``text_format`` to
    :func:`arkruntime.common._parsing._responses.parse_response`."""

    parsed: Optional[ContentType] = None


# Upstream implementations use a discriminated union here to fold in refusal
# content. ark-apis doesn't expose refusal in this API, so the union
# collapses to a single arm.
ParsedContent: TypeAlias = ParsedResponseOutputText[ContentType]


class ParsedResponseOutputMessage(
    ItemOutputMessage, GenericModel, Generic[ContentType]
):
    if TYPE_CHECKING:
        content: Optional[List[ParsedContent[ContentType]]]  # type: ignore[assignment]
    else:
        content: Optional[List[ParsedContent]] = None


class ParsedResponseFunctionToolCall(ItemFunctionToolCall):
    """``function_call`` output augmented with deserialised
    ``parsed_arguments`` (populated when the matching tool was strict or
    a :class:`ResponsesPydanticFunctionTool`)."""

    parsed_arguments: object = None

    __api_exclude__ = {"parsed_arguments"}


# ark-apis only models message / function_call / reasoning /
# computer_call / file_search_call / web_search_call output items. The
# parser passes the latter four through untouched, so the typed
# Parsed-output union only needs the two augmented variants. Other
# items remain typed as their original `OutputItem` and arrive on the
# list as-is.
ParsedResponseOutputItem: TypeAlias = (
    "ParsedResponseOutputMessage[ContentType] | ParsedResponseFunctionToolCall | object"
)


class ParsedResponse(Response, GenericModel, Generic[ContentType]):
    if TYPE_CHECKING:
        output: List["ParsedResponseOutputItem[ContentType]"]  # type: ignore[assignment]
    else:
        output: List[object] = []  # type: ignore[assignment]

    @property
    def output_parsed(self) -> Optional[ContentType]:
        for output in self.output:
            if getattr(output, "type", None) == "message":
                for content in (getattr(output, "content", None) or []):
                    if (
                        getattr(content, "type", None) == "output_text"
                        and getattr(content, "parsed", None)
                    ):
                        return content.parsed
        return None
