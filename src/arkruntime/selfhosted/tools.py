# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import base64
import glob as globlib
import json
import mimetypes
import os
import re
import signal
import stat
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

from .types import DEFAULT_TOOL_TIMEOUT_SECONDS, ContentBlock

MAX_OUTPUT_BYTES = 100000
DEFAULT_MAX_MEDIA_FILE_BYTES = 7 << 20
DEFAULT_READ_LINES = 2000
MAX_READ_LINE_CHARS = 2000
MAX_SEARCH_MATCHES = 1000
_SENSITIVE_ENV_PREFIXES = (
    "AIME_",
    "ARK_",
    "MA_",
    "X_CODE_",
    "ANTHROPIC_",
    "OPENAI_",
    "AWS_",
    "AZURE_",
    "GOOGLE_",
)
_SENSITIVE_ENV_NAMES = {
    "VOLC_ACCESSKEY",
    "VOLC_SECRETKEY",
    "BYTEPLUS_ACCESSKEY",
    "BYTEPLUS_SECRETKEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASSWD",
    "PRIVATE_KEY",
    "API_KEY",
    "ACCESS_KEY",
    "SECRET_KEY",
    "JWT",
    "PAT",
}
_SENSITIVE_ENV_SUFFIXES = (
    "_TOKEN",
    "_SECRET",
    "_PASSWORD",
    "_PASSWD",
    "_PRIVATE_KEY",
    "_API_KEY",
    "_ACCESS_KEY",
    "_SECRET_KEY",
    "_JWT",
    "_PAT",
)


@dataclass
class ToolResult:
    content: Iterable[ContentBlock]
    is_error: bool = False


class Tool:
    """Tool contract; the runner enforces timeouts and tools should release promptly on cancellation."""

    name: str

    def execute(self, tool_input: Any, context: "ToolContext") -> ToolResult:
        raise NotImplementedError


@dataclass
class ToolContext:
    workdir: str
    env: Optional[Dict[str, str]] = None
    unrestricted_paths: bool = False
    tool_timeout_seconds: float = DEFAULT_TOOL_TIMEOUT_SECONDS
    cancel_event: Any = None
    max_input_file_bytes: int = MAX_OUTPUT_BYTES
    # 0 follows max_input_file_bytes; a negative value disables the media limit.
    max_media_file_bytes: int = DEFAULT_MAX_MEDIA_FILE_BYTES


class FunctionTool(Tool):
    def __init__(self, name: str, fn: Callable[[Any, ToolContext], ToolResult]) -> None:
        self.name = name
        self._fn = fn

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        return self._fn(tool_input, context)


class ToolSet:
    def __init__(self, tools: Optional[Iterable[Tool]] = None) -> None:
        self._tools: Dict[str, Tool] = {}
        for tool in tools or []:
            self.add(tool)

    def add(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError("tool name must not be empty")
        self._tools[tool.name] = tool

    def has(self, name: str) -> bool:
        return name in self._tools

    def execute(self, name: str, tool_input: Any, context: ToolContext) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return error_result(f"tool {name!r} is not registered")
        try:
            return tool.execute(tool_input, context)
        except Exception as exc:  # noqa: BLE001 - tool errors must be reported, not raised.
            return error_result(str(exc))


class BashTool(Tool):
    name = "bash"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        command = str(args.get("command") or args.get("cmd") or "")
        if not command:
            return error_result("bash command is required")
        env = _scrubbed_env(context.env)
        proc = subprocess.Popen(  # noqa: S602 - this is the explicit bash tool contract.
            command,
            shell=True,
            cwd=context.workdir,
            env=env,
            text=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        output = _BoundedOutput(MAX_OUTPUT_BYTES)
        reader = threading.Thread(target=_drain_output, args=(proc.stdout, output), daemon=True)
        reader.start()
        deadline = time.monotonic() + max(context.tool_timeout_seconds, 0)
        failure = ""
        while proc.poll() is None:
            if _is_cancelled(context):
                failure = "tool execution canceled"
                _kill_process(proc)
                break
            if context.tool_timeout_seconds > 0 and time.monotonic() >= deadline:
                failure = f"tool execution timed out after {context.tool_timeout_seconds:g}s"
                _kill_process(proc)
                break
            time.sleep(0.05)
        proc.wait()
        reader.join(timeout=1)
        text = output.text()
        if failure:
            return error_result(f"{failure}\n{text}".rstrip())
        if proc.returncode != 0:
            text = f"exit code {proc.returncode}\n{text}" if text else f"exit code {proc.returncode}"
        return text_result(text, is_error=proc.returncode != 0)


class ReadFileTool(Tool):
    name = "read"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        try:
            path = _safe_path(context, _file_path(args))
        except ValueError as exc:
            return error_result(str(exc))
        view_range = args.get("view_range")
        if view_range in (None, []):
            view_range = None
        elif not isinstance(view_range, (list, tuple)) or len(view_range) != 2:
            return error_result("view_range must be [start_line, end_line]")
        try:
            offset = _optional_integer(args, "offset")
            limit = _optional_integer(args, "limit")
            if view_range is not None:
                start_line = _integer_value(view_range[0], "view_range")
                end_line = _integer_value(view_range[1], "view_range")
        except ValueError as exc:
            return error_result(str(exc))
        if view_range is not None and (offset is not None or limit is not None):
            return error_result("view_range cannot be combined with offset or limit")
        media = _detect_read_media(path)
        if media is not None:
            if view_range is not None or offset is not None or limit is not None:
                return error_result("view_range, offset, and limit are only supported for text files")
            size = os.path.getsize(path)
            media_limit = context.max_media_file_bytes
            if media_limit == 0:
                media_limit = context.max_input_file_bytes
            if media_limit > 0 and size > media_limit:
                return error_result(f"media file too large: {size} bytes")
            block_type, media_type = media
            with open(path, "rb") as file:
                raw = file.read(media_limit + 1) if media_limit > 0 else file.read()
            if media_limit > 0 and len(raw) > media_limit:
                return error_result(f"media file too large: {max(size, len(raw))} bytes")
            data = base64.b64encode(raw).decode("ascii")
            return ToolResult(
                [ContentBlock(type=block_type, source={"type": "base64", "media_type": media_type, "data": data})]
            )
        text_limit = context.max_input_file_bytes if context.max_input_file_bytes > 0 else MAX_OUTPUT_BYTES
        size = os.path.getsize(path)
        if text_limit > 0 and size > text_limit:
            return error_result(f"file too large: {size} bytes")
        raw = Path(path).read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return error_result("binary file cannot be read directly")
        if view_range is not None:
            lines = text.split("\n")
            start = max(0, start_line - 1)
            if start >= len(lines):
                return text_result("")
            end = len(lines)
            if end_line > 0:
                end = min(end, end_line)
            if end < start:
                return error_result(f"view_range end line {end_line} is before start line {start_line}")
            return text_result("\n".join(lines[start:end]))
        if offset is not None and offset < 1:
            return error_result(f"offset is the 1-based start line and must be >= 1, got {offset}")
        return text_result(_render_read_lines(text, offset, limit))


def _file_path(args: Mapping[str, Any]) -> str:
    path = ""
    for name in ("file_path", "path", "file"):
        value = args.get(name)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
        candidate = value or ""
        if not candidate:
            continue
        if path and path != candidate:
            raise ValueError("file_path, path, and file must not conflict")
        path = candidate
    if not path:
        raise ValueError("file_path is required")
    return path


def _integer_value(value: Any, name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"[+-]?\d+", value):
        return int(value)
    raise ValueError(f"{name} must be an integer")


def _optional_integer(args: Mapping[str, Any], name: str) -> Optional[int]:
    if name not in args or args[name] is None:
        return None
    return _integer_value(args[name], name)


def _render_read_lines(text: str, offset: Optional[int], limit: Optional[int]) -> str:
    lines = text.split("\n")
    if lines and lines[-1] == "" and text.endswith("\n"):
        lines.pop()
    start = (offset or 1) - 1
    start = min(start, len(lines))
    count = limit if limit is not None and limit > 0 else DEFAULT_READ_LINES
    end = min(start + count, len(lines))
    output = []
    for index in range(start, end):
        line = lines[index]
        if len(line) > MAX_READ_LINE_CHARS:
            line = f"{line[:MAX_READ_LINE_CHARS]} [line truncated]"
        output.append(f"{index + 1:6d}\t{line}\n")
    if end < len(lines):
        output.append(f"\n[truncated: showing lines {start + 1}-{end} of {len(lines)}]\n")
    return "".join(output)


def _detect_read_media(path: str) -> Optional[tuple[str, str]]:
    with open(path, "rb") as file:
        header = file.read(512)
    if header.startswith(b"\xff\xd8\xff"):
        return "image", "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image", "image/png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image", "image/gif"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image", "image/webp"
    if header.startswith(b"%PDF-"):
        return "document", "application/pdf"
    if not _looks_binary(header):
        return None
    media_type = mimetypes.guess_type(path)[0] or ""
    if media_type in ("image/jpeg", "image/png", "image/gif", "image/webp"):
        return "image", media_type
    if media_type == "application/pdf":
        return "document", media_type
    return None


def _looks_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


class WriteFileTool(Tool):
    name = "write"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        try:
            raw_path = _file_path(args)
            path = _safe_path(context, raw_path)
        except ValueError as exc:
            return error_result(str(exc))
        content = str(args.get("content") or "")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        verified = _safe_path(context, raw_path)
        if verified != path:
            raise ValueError("path resolution changed while writing")
        _write_file_atomically(path, content.encode("utf-8"), 0o600)
        return text_result(f"wrote {len(content)} bytes")


class EditFileTool(Tool):
    name = "edit"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        try:
            raw_path = _file_path(args)
            path = _safe_path(context, raw_path)
        except ValueError as exc:
            return error_result(str(exc))
        old = str(args.get("old_string") or args.get("old") or "")
        new = str(args.get("new_string") or args.get("new") or "")
        if not old:
            return error_result("old_string is required")
        data = Path(path).read_text(encoding="utf-8")
        if old not in data:
            return error_result("old_string was not found")
        mode = stat.S_IMODE(os.stat(path).st_mode)
        verified = _safe_path(context, raw_path)
        if verified != path:
            raise ValueError("path resolution changed while editing")
        _write_file_atomically(path, data.replace(old, new, 1).encode("utf-8"), mode)
        return text_result("edited")


class GlobTool(Tool):
    name = "glob"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        pattern = str(args.get("pattern") or "")
        if not pattern:
            return error_result("pattern is required")
        root = Path(context.workdir).resolve()
        matches = []
        for match in globlib.glob(str(root / pattern), recursive=True):
            if _is_cancelled(context):
                return error_result("tool execution canceled")
            try:
                resolved = Path(match).resolve()
                if context.unrestricted_paths or resolved == root or root in resolved.parents:
                    matches.append(str(resolved.relative_to(root)) if root in resolved.parents else str(resolved))
                    if len(matches) >= MAX_SEARCH_MATCHES:
                        break
            except (OSError, ValueError):
                continue
        return text_result(_truncate("\n".join(sorted(matches))))


class GrepTool(Tool):
    name = "grep"

    def execute(self, tool_input: Any, context: ToolContext) -> ToolResult:
        args = _as_mapping(tool_input)
        pattern = str(args.get("pattern") or args.get("query") or "")
        target = str(args.get("path") or ".")
        if not pattern:
            return error_result("pattern is required")
        root = _safe_path(context, target)
        rx = re.compile(pattern)
        lines = []
        paths: Iterable[str] = [root]
        if os.path.isdir(root):
            paths = (os.path.join(base, name) for base, _, names in os.walk(root) for name in names)
        for path in paths:
            if _is_cancelled(context):
                return error_result("tool execution canceled")
            try:
                verified = _safe_path(context, path)
                with open(verified, "r", encoding="utf-8", errors="replace") as f:
                    for number, line in enumerate(f, 1):
                        if _is_cancelled(context):
                            return error_result("tool execution canceled")
                        if rx.search(line):
                            rel = os.path.relpath(path, context.workdir)
                            lines.append(f"{rel}:{number}:{line.rstrip()}")
                            if len(lines) >= 200 or sum(len(value) + 1 for value in lines) >= MAX_OUTPUT_BYTES:
                                return text_result(_truncate("\n".join(lines)))
            except (OSError, ValueError):
                continue
        return text_result("\n".join(lines))


def default_toolset() -> ToolSet:
    return ToolSet([BashTool(), ReadFileTool(), WriteFileTool(), EditFileTool(), GlobTool(), GrepTool()])


def text_result(text: str, *, is_error: bool = False) -> ToolResult:
    return ToolResult([ContentBlock(type="text", text=text)], is_error=is_error)


def error_result(text: str) -> ToolResult:
    return text_result(text, is_error=True)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            return {"command": value}
        if isinstance(parsed, Mapping):
            return parsed
    return {}


def _safe_path(context: ToolContext, path: str) -> str:
    if not path:
        raise ValueError("path is required")
    root = Path(context.workdir).resolve()
    target = Path(path)
    if not target.is_absolute():
        target = root / target
    resolved = target.resolve()
    if context.unrestricted_paths:
        return str(resolved)
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes workdir: {path}")
    return str(resolved)


def _truncate(text: str, limit: int = 100000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... truncated ..."


def _is_cancelled(context: ToolContext) -> bool:
    return bool(context.cancel_event and context.cancel_event.is_set())


def _is_sensitive_env_key(key: str) -> bool:
    upper = key.strip().upper()
    return (
        upper.startswith(_SENSITIVE_ENV_PREFIXES)
        or upper in _SENSITIVE_ENV_NAMES
        or upper.endswith(_SENSITIVE_ENV_SUFFIXES)
    )


def _scrubbed_env(extra: Optional[Mapping[str, str]]) -> Dict[str, str]:
    source = dict(os.environ) if extra is None else dict(extra)
    return {key: value for key, value in source.items() if not _is_sensitive_env_key(key)}


def _write_file_atomically(path: str, data: bytes, mode: int) -> None:
    parent = str(Path(path).parent)
    fd, tmp = tempfile.mkstemp(prefix=".ark-write-", dir=parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as output:
            fd = -1
            output.write(data)
        os.replace(tmp, path)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            os.remove(tmp)
        except FileNotFoundError:
            pass


class _BoundedOutput:
    _MARKER = b"\n... truncated ..."

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._data = bytearray()
        self._truncated = False
        self._lock = threading.Lock()

    def append(self, chunk: bytes) -> None:
        with self._lock:
            remaining = max(0, self._limit - len(self._MARKER) - len(self._data))
            if remaining > 0:
                self._data.extend(chunk[:remaining])
            if len(chunk) > remaining:
                self._truncated = True

    def text(self) -> str:
        with self._lock:
            text = bytes(self._data).decode("utf-8", errors="replace")
            if self._truncated:
                text += self._MARKER.decode("ascii")
            return text


def _drain_output(stream: Any, output: _BoundedOutput) -> None:
    if stream is None:
        return
    try:
        while True:
            chunk = stream.read(65536)
            if not chunk:
                return
            output.append(chunk)
    finally:
        stream.close()


def _kill_process(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (OSError, AttributeError):
        proc.kill()
