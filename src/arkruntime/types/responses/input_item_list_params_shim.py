# Copyright (c) 2025 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0
# License text: https://github.com/volcengine/ark-runtime-python/blob/main/LICENSE

from __future__ import annotations

from typing import List
from typing_extensions import Literal, TypedDict

from arkruntime.types.responses.response_includable import ResponseIncludable as IncludeOption

__all__ = ["InputItemListParams"]


class InputItemListParams(TypedDict, total=False):
    after: str
    """An item ID to list items after, used in pagination."""

    before: str
    """An item ID to list items before, used in pagination."""

    include: List[IncludeOption]
    """Additional fields to include in the response.

    See the `include` parameter for Response creation above for more information.
    """

    limit: int
    """A limit on the number of objects to be returned.

    Limit can range between 1 and 100, and the default is 20.
    """

    order: Literal["asc", "desc"]
    """The order to return the input items in. Default is `desc`.

    - `asc`: Return the input items in ascending order.
    - `desc`: Return the input items in descending order.
    """
