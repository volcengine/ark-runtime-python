# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from typing import Optional

from .chat_completion_message_tool_call import ChatCompletionMessageToolCall
from .chat_completion_message_tool_call_function import (
    ChatCompletionMessageToolCallFunction,
)

__all__ = ["ParsedFunctionToolCall", "ParsedFunction"]

# we need to disable this check because we're overriding properties
# with subclasses of their types which is technically unsound as
# properties can be mutated.
# pyright: reportIncompatibleVariableOverride=false


class ParsedFunction(ChatCompletionMessageToolCallFunction):
    parsed_arguments: Optional[object] = None
    """
    The arguments to call the function with.
    """


class ParsedFunctionToolCall(ChatCompletionMessageToolCall):
    function: ParsedFunction
    """The function that the model called."""
