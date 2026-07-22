"""Small serialization helpers shared by the managed-agents resource wrappers.

The upstream `_utils.maybe_transform` helper expects a `TypedDict`
descriptor as its second argument. The managed-agents `types/` layer only
emits pydantic `BaseModel` classes (no companion `*Param` TypedDicts —
those are generated only when a `gen/py/codegen-<api>.yml` exists in
ark-apis, which is not the case for this API family). So the wrappers use
this helper instead: recursively convert nested pydantic instances to
plain dicts, drop `NOT_GIVEN` sentinels, and preserve everything else
as-is.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping

from pydantic import BaseModel

from ._types import NOT_GIVEN


def _dump(value: Any) -> Any:
    """Recursively coerce a value into JSON-serialisable form.

    - `NOT_GIVEN` → dropped by the caller (returned as-is; caller filters).
    - `pydantic.BaseModel` → `.model_dump(exclude_unset=True, by_alias=True)`
      so unset Optional fields don't leak `null` onto the wire (server-side
      is Anthropic-flavoured `omit == null == unset`).
    - `enum.Enum` → its `.value`. Handles enum-typed fields (e.g.
      `EnvConfigType.CLOUD` → `"cloud"`) that get passed positionally.
    - `list` / `tuple` → element-wise recursion.
    - `dict` → key/value recursion.
    - primitives → passthrough.
    """
    if isinstance(value, BaseModel):
        return _dump(value.model_dump(exclude_unset=True, by_alias=True))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_dump(v) for v in value]
    if isinstance(value, Mapping):
        return {k: _dump(v) for k, v in value.items() if v is not NOT_GIVEN}
    return value


def dump_body(body: Mapping[str, Any]) -> dict:
    """Turn a wrapper's `{field: value}` dict into a JSON-safe request body.

    Drops keys whose value is `NOT_GIVEN` (SDK sentinel for "argument not
    provided") and recursively serialises pydantic models, so the caller
    can pass model instances directly (e.g. `EnvConfig(type="cloud")`)
    without pre-dumping them.
    """
    return {k: _dump(v) for k, v in body.items() if v is not NOT_GIVEN}
