# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import base64
import threading
import time

import pytest

from arkruntime.selfhosted.tools import (
    BashTool,
    EditFileTool,
    GrepTool,
    ReadFileTool,
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


@pytest.mark.parametrize(
    "name, data, block_type, media_type",
    [
        ("photo.jpg", b"\xff\xd8\xff\xe0data", "image", "image/jpeg"),
        ("image.png", b"\x89PNG\r\n\x1a\ndata", "image", "image/png"),
        ("image.gif", b"GIF89adata", "image", "image/gif"),
        ("image.webp", b"RIFF\x04\x00\x00\x00WEBPdata", "image", "image/webp"),
        ("document.pdf", b"%PDF-1.7\ndata", "document", "application/pdf"),
    ],
)
def test_read_returns_native_media_block(tmp_path, name, data, block_type, media_type) -> None:
    (tmp_path / name).write_bytes(data)

    result = ReadFileTool().execute({"file_path": name}, ToolContext(workdir=str(tmp_path)))

    assert not result.is_error
    block = list(result.content)[0]
    assert block.type == block_type
    assert block.source == {
        "type": "base64",
        "media_type": media_type,
        "data": base64.b64encode(data).decode("ascii"),
    }


def test_read_rejects_ranges_and_oversized_media(tmp_path) -> None:
    data = b"\x89PNG\r\n\x1a\ndata"
    (tmp_path / "image.png").write_bytes(data)
    tool = ReadFileTool()

    ranged = tool.execute({"path": "image.png", "limit": 1}, ToolContext(workdir=str(tmp_path)))
    invalid = tool.execute({"path": "image.png", "limit": "10KB"}, ToolContext(workdir=str(tmp_path)))
    oversized = tool.execute(
        {"path": "image.png"}, ToolContext(workdir=str(tmp_path), max_media_file_bytes=len(data) - 1)
    )

    assert ranged.is_error
    assert _text(ranged) == "view_range, offset, and limit are only supported for text files"
    assert invalid.is_error
    assert _text(invalid) == "limit must be an integer"
    assert oversized.is_error
    assert _text(oversized) == f"media file too large: {len(data)} bytes"


def test_read_uses_managed_agent_line_range(tmp_path) -> None:
    (tmp_path / "example.txt").write_text("a\nb\nc\nd\n")
    tool = ReadFileTool()
    context = ToolContext(workdir=str(tmp_path))

    whole = tool.execute({"file_path": "example.txt"}, context)
    ranged = tool.execute({"file_path": "example.txt", "offset": 2, "limit": 2}, context)
    invalid = tool.execute({"file_path": "example.txt", "offset": 0}, context)

    assert not whole.is_error
    assert _text(whole) == "     1\ta\n     2\tb\n     3\tc\n     4\td\n"
    assert not ranged.is_error
    assert _text(ranged) == "     2\tb\n     3\tc\n\n[truncated: showing lines 2-3 of 4]\n"
    assert invalid.is_error
    assert _text(invalid) == "offset is the 1-based start line and must be >= 1, got 0"


def test_read_marks_truncated_lines(tmp_path) -> None:
    (tmp_path / "long.txt").write_text("a" * 2001)

    result = ReadFileTool().execute({"file_path": "long.txt"}, ToolContext(workdir=str(tmp_path)))

    assert not result.is_error
    assert _text(result) == f"     1\t{'a' * 2000} [line truncated]\n"


def test_read_keeps_legacy_inputs_without_ambiguity(tmp_path) -> None:
    (tmp_path / "example.txt").write_text("a\nb\nc\n")
    tool = ReadFileTool()
    context = ToolContext(workdir=str(tmp_path))

    for tool_input in (
        {"path": "example.txt"},
        {"file": "example.txt"},
        {"file_path": "example.txt", "path": "example.txt"},
    ):
        assert not tool.execute(tool_input, context).is_error
    legacy_range = tool.execute({"file_path": "example.txt", "view_range": [2, 3]}, context)
    path_conflict = tool.execute({"file_path": "example.txt", "path": "other.txt"}, context)
    range_conflict = tool.execute({"file_path": "example.txt", "view_range": [1, 1], "offset": 1}, context)

    assert not legacy_range.is_error
    assert _text(legacy_range) == "b\nc"
    assert path_conflict.is_error
    assert _text(path_conflict) == "file_path, path, and file must not conflict"
    assert range_conflict.is_error
    assert _text(range_conflict) == "view_range cannot be combined with offset or limit"


@pytest.mark.parametrize("path_key", ["file_path", "path", "file"])
def test_file_tools_accept_path_aliases(tmp_path, path_key) -> None:
    context = ToolContext(workdir=str(tmp_path))
    source = tmp_path / "source.txt"
    source.write_text("old")

    read = ReadFileTool().execute({path_key: "source.txt"}, context)
    write = WriteFileTool().execute({path_key: "written.txt", "content": "created"}, context)
    edit = EditFileTool().execute(
        {path_key: "source.txt", "old_string": "old", "new_string": "new"},
        context,
    )

    assert not read.is_error
    assert not write.is_error
    assert not edit.is_error
    assert (tmp_path / "written.txt").read_text() == "created"
    assert source.read_text() == "new"


@pytest.mark.parametrize("tool", [ReadFileTool(), WriteFileTool(), EditFileTool()])
def test_file_tools_validate_path_aliases(tmp_path, tool) -> None:
    context = ToolContext(workdir=str(tmp_path))
    (tmp_path / "example.txt").write_text("old")
    common = {
        "file_path": "example.txt",
        "path": "example.txt",
        "file": "example.txt",
        "content": "new",
        "old_string": "old",
        "new_string": "new",
    }

    same = tool.execute(common, context)
    conflict = tool.execute({**common, "path": "other.txt"}, context)
    missing = tool.execute({"content": "new", "old_string": "old", "new_string": "new"}, context)

    assert not same.is_error
    assert conflict.is_error
    assert _text(conflict) == "file_path, path, and file must not conflict"
    assert missing.is_error
    assert _text(missing) == "file_path is required"


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
