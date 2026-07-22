# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Hand-written re-exports for the chat API.

Pulled into ``__init__.py`` via a trailing
``from ._init_extras_shim import *`` block emitted by the ark-apis
generator. Preserved across regen by the Makefile rsync
``--exclude='*_shim.py'`` rule.
"""

from __future__ import annotations

# Backwards-compatible aliases. The generator emits longer canonical names
# (e.g. ChatCompletionResponse) but downstream consumers and historical SDK
# users address these objects by their short-form aliases.
from .chat_completion_response import ChatCompletionResponse as ChatCompletion
from .chat_completion_stream_response import (
    ChatCompletionStreamResponse as ChatCompletionChunk,
)
from .chat_completion_response_message import (
    ChatCompletionResponseMessage as ChatCompletionMessage,
)
from .chat_completion_request_message_param import (
    ChatCompletionRequestMessageParam as ChatCompletionMessageParam,
)
from .chat_completion_request_user_message_param import (
    ChatCompletionRequestUserMessageParam as ChatCompletionUserMessageParam,
)
from .chat_completion_request_system_message_param import (
    ChatCompletionRequestSystemMessageParam as ChatCompletionSystemMessageParam,
)
from .chat_completion_request_assistant_message_param import (
    ChatCompletionRequestAssistantMessageParam as ChatCompletionAssistantMessageParam,
)
from .chat_completion_request_tool_message_param import (
    ChatCompletionRequestToolMessageParam as ChatCompletionToolMessageParam,
)
from .chat_completion_tool_choice_param import (
    ChatCompletionToolChoiceParam as ChatCompletionToolChoiceOptionParam,
)
from .chat_completion_request_param import (
    ChatCompletionRequestParam as CompletionCreateParams,
)

# SDK-only siblings (not generated).
from .parsed_chat_completion_shim import (
    ParsedChoice,
    ParsedChatCompletion,
    ParsedChatCompletionMessage,
)
from .parsed_function_tool_call_shim import (
    ParsedFunction,
    ParsedFunctionToolCall,
)

__all__ = [
    "ChatCompletion",
    "ChatCompletionChunk",
    "ChatCompletionMessage",
    "ChatCompletionMessageParam",
    "ChatCompletionUserMessageParam",
    "ChatCompletionSystemMessageParam",
    "ChatCompletionAssistantMessageParam",
    "ChatCompletionToolMessageParam",
    "ChatCompletionToolChoiceOptionParam",
    "CompletionCreateParams",
    "ParsedChoice",
    "ParsedChatCompletion",
    "ParsedChatCompletionMessage",
    "ParsedFunction",
    "ParsedFunctionToolCall",
]
