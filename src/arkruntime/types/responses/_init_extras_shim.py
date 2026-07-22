# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Hand-written re-exports for the responses API.

Pulled into ``__init__.py`` via a trailing
``from ._init_extras_shim import *`` block emitted by the ark-apis
generator. Preserved across regen by the Makefile rsync
``--exclude='*_shim.py'`` rule.
"""

from __future__ import annotations

# Hand-written sibling models.
from .input_item_list_params_shim import InputItemListParams

# Cross-SDK aliases. ark-apis renames a few Responses types relative
# to the upstream SDK; the SDK's parsing helpers and external
# consumers still address them by the upstream short names.
from .output_content_item_text import OutputContentItemText as ResponseOutputText
from .item_output_message import ItemOutputMessage as ResponseOutputMessage
from .item_function_tool_call import ItemFunctionToolCall as ResponseFunctionToolCall
from .text_format_param import TextFormatParam as ResponseFormatTextConfigParam

# Parsed-* sibling models for response auto-parsing.
from .parsed_response_shim import (
    ParsedContent,
    ParsedResponse,
    ParsedResponseOutputItem,
    ParsedResponseOutputMessage,
    ParsedResponseOutputText,
    ParsedResponseFunctionToolCall,
)

__all__ = [
    "InputItemListParams",
    "ResponseOutputText",
    "ResponseOutputMessage",
    "ResponseFunctionToolCall",
    "ResponseFormatTextConfigParam",
    "ParsedContent",
    "ParsedResponse",
    "ParsedResponseOutputItem",
    "ParsedResponseOutputMessage",
    "ParsedResponseOutputText",
    "ParsedResponseFunctionToolCall",
]
