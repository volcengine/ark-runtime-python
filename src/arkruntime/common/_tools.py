# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from typing import Any, Dict, cast

import pydantic

from ..types.chat import ChatCompletionToolParam
from ..types.chat.function_object_param import FunctionObjectParam as FunctionDefinition
from ..types.responses.function_tool_param import (
    FunctionToolParam as ResponsesFunctionToolParam,
)
from ._pydantic import to_strict_json_schema


class PydanticFunctionTool(Dict[str, Any]):
    """Dictionary wrapper so we can pass the given base model
    throughout the entire request stack without having to special
    case it.
    """

    model: type[pydantic.BaseModel]

    def __init__(self, defn: FunctionDefinition, model: type[pydantic.BaseModel]) -> None:
        super().__init__(defn)
        self.model = model

    def cast(self) -> FunctionDefinition:
        return cast(FunctionDefinition, self)


class ResponsesPydanticFunctionTool(Dict[str, Any]):
    """Responses-API counterpart to :class:`PydanticFunctionTool`.

    The Responses API encodes function tools with a flatter shape than
    Chat Completions — name, parameters and strict live directly on the
    tool dict instead of nested under ``function``. We wrap that dict and
    keep a reference to the pydantic model so the response parser can
    deserialise ``arguments`` back into the original type.
    """

    model: type[pydantic.BaseModel]

    def __init__(
        self,
        tool: ResponsesFunctionToolParam,
        model: type[pydantic.BaseModel],
    ) -> None:
        super().__init__(tool)
        self.model = model

    def cast(self) -> ResponsesFunctionToolParam:
        return cast(ResponsesFunctionToolParam, self)


def pydantic_function_tool(
    model: type[pydantic.BaseModel],
    *,
    name: str | None = None,  # inferred from class name by default
    description: str | None = None,  # inferred from class docstring by default
) -> ChatCompletionToolParam:
    if description is None:
        # note: we intentionally don't use `.getdoc()` to avoid
        # including pydantic's docstrings
        description = model.__doc__

    function = PydanticFunctionTool(
        {
            "name": name or model.__name__,
            "strict": True,
            "parameters": to_strict_json_schema(model),
        },
        model,
    ).cast()

    if description is not None:
        function["description"] = description

    return {
        "type": "function",
        "function": function,
    }
