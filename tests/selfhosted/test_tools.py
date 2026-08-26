# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import threading
import time

import pytest

from arkruntime.selfhosted.tools import (
    BashTool,
    EditFileTool,
    GrepTool,
    ToolContext,
    WriteFileTool,
    _is_sensitive_env_key,
)


def _text(result) -> str:
    return "".join(block.text for block in result.content)


def _env_name(*parts: str) -> str:
    return "_".join(parts)


def test_bash_scrubs_inherited_and_explicit_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(_env_name("ARK", "API", "KEY"), "redacted")
    monkeypatch.setenv("SAFE_INHERITED", "safe")
    context = ToolContext(
        workdir=str(tmp_path),
        env={
            _env_name("ARK", "API", "KEY"): "redacted",
            "SAFE_EXPLICIT": "ok",
        },
    )

    result = BashTool().execute(
        {"command": ('printf \'%s/%s/%s\' "${ARK_API_KEY-unset}" "$SAFE_INHERITED" "$SAFE_EXPLICIT"')},
        context,
    )

    assert not result.is_error
    assert _text(result) == "unset//ok"


def test_bash_scrubs_extended_credential_names() -> None:
    assert _is_sensitive_env_key(_env_name("AIME", "SESSION"))
    assert _is_sensitive_env_key(_env_name("X", "CODE", "AUTH"))
    assert _is_sensitive_env_key(_env_name("GITHUB", "JWT"))
    assert _is_sensitive_env_key(_env_name("GITHUB", "PAT"))
    assert not _is_sensitive_env_key("SAFE_VALUE")


def test_bash_honors_worker_cancellation(tmp_path) -> None:
    canceled = threading.Event()
    context = ToolContext(workdir=str(tmp_path), cancel_event=canceled, tool_timeout_seconds=10)
    timer = threading.Timer(0.1, canceled.set)
    timer.start()
    started = time.monotonic()
    try:
        result = BashTool().execute({"command": "sleep 10"}, context)
    finally:
        timer.cancel()

    assert time.monotonic() - started < 2
    assert result.is_error
    assert "canceled" in _text(result)


def test_grep_skips_symlink_that_escapes_workdir(tmp_path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("SELFHOST_SECRET_MARKER\n")
    (tmp_path / "escape.txt").symlink_to(outside / "secret.txt")

    result = GrepTool().execute(
        {"path": ".", "pattern": "SELFHOST_SECRET_MARKER"},
        ToolContext(workdir=str(tmp_path)),
    )

    assert not result.is_error
    assert "SELFHOST_SECRET_MARKER" not in _text(result)


@pytest.mark.parametrize(
    "tool, tool_input",
    [
        (WriteFileTool(), {"path": "example.txt", "content": "new"}),
        (EditFileTool(), {"path": "example.txt", "old_string": "old", "new_string": "new"}),
    ],
)
def test_file_mutation_keeps_old_content_when_atomic_replace_fails(tmp_path, monkeypatch, tool, tool_input) -> None:
    target = tmp_path / "example.txt"
    target.write_text("old")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr("arkruntime.selfhosted.tools.os.replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        tool.execute(tool_input, ToolContext(workdir=str(tmp_path)))

    assert target.read_text() == "old"
