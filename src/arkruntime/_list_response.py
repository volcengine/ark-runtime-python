# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re

import httpx


def normalize_list_response(data: object, response: httpx.Response, base_path: str) -> object:
    """Adapt legacy null pages only for files and session resources GETs."""
    if response.request.method != "GET" or not response.is_success:
        return data
    path = response.request.url.path
    prefix = base_path.rstrip("/")
    is_files = path == prefix + "/files"
    is_resources = re.fullmatch(re.escape(prefix) + r"/sessions/[^/]+/resources", path) is not None
    if not (is_files or is_resources):
        return data
    if data is None:
        if is_files:
            return {"object": "file", "data": [], "first_id": "", "last_id": "", "has_more": False}
        return {"data": []}
    if isinstance(data, dict) and "data" in data and data["data"] is None:
        return {**data, "data": []}
    return data
