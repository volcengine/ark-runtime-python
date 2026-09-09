# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import asyncio
from importlib.metadata import version
from pathlib import Path

import httpx
import pytest

from arkruntime import Ark, AsyncArk, _version


@pytest.mark.parametrize("custom", [None, "my-app/2.0"])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_user_agent_on_requests(custom: str | None, asynchronous: bool) -> None:
    requests = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"id": "test-file", "object": "file"})

    headers = {"User-Agent": custom} if custom else {}
    transport = httpx.MockTransport(handle)
    if asynchronous:

        async def run() -> None:
            async with AsyncArk(api_key="placeholder", http_client=httpx.AsyncClient(transport=transport)) as client:
                await client.files.retrieve("test-file", extra_headers=headers)

        asyncio.run(run())
    else:
        with Ark(api_key="placeholder", http_client=httpx.Client(transport=transport)) as client:
            client.files.retrieve("test-file", extra_headers=headers)

    assert len(requests) == 1
    assert requests[0].headers.get_list("User-Agent") == [custom or "ark-runtime-python/" + version("arkruntime")]


def test_checkout_version_takes_precedence_over_installed_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "src" / "arkruntime" / "_version.py"
    monkeypatch.setattr(_version, "__file__", str(source))
    monkeypatch.setattr(_version, "version", lambda name: "0.0.1")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.example]\nversion = "9.9.9"\n[project]\nname = "arkruntime"\nversion = "2.3.4rc1"\n'
        '[tool.other]\nversion = "8.8.8"\n',
        encoding="utf-8",
    )
    assert _version._get_version() == "2.3.4rc1"


def test_installed_version_uses_distribution_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_version, "__file__", str(tmp_path / "site-packages" / "arkruntime" / "_version.py"))

    def metadata_version(name: str) -> str:
        assert name == "arkruntime"
        return "3.4.5"

    monkeypatch.setattr(_version, "version", metadata_version)
    assert _version._get_version() == "3.4.5"


def test_missing_source_version_does_not_use_stale_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_version, "__file__", str(tmp_path / "src" / "arkruntime" / "_version.py"))
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "arkruntime"\n', encoding="utf-8")
    with pytest.raises(RuntimeError, match="Expected a static project.version"):
        _version._get_version()
