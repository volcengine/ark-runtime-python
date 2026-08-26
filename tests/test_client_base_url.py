# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from arkruntime import Ark


def _test_credential() -> str:
    return "placeholder"


def test_client_uses_production_base_url_by_default() -> None:
    client = Ark(api_key=_test_credential())
    try:
        assert str(client._base_url).rstrip("/") == "https://ark.cn-beijing.volces.com/api/v3"
    finally:
        client.close()


def test_client_accepts_base_url_override() -> None:
    client = Ark(
        api_key=_test_credential(),
        base_url="https://example.com/api/v3",
    )
    try:
        assert str(client._base_url).rstrip("/") == "https://example.com/api/v3"
    finally:
        client.close()
