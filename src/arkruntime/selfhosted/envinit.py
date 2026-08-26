# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
import os
import re
import shutil
import stat
import tarfile
import tempfile
import zipfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .types import Session, SkillRef

DEFAULT_MAX_ARCHIVE_BYTES = 128 << 20
DEFAULT_MAX_EXTRACTED_BYTES = 512 << 20
DEFAULT_MAX_ARCHIVE_ENTRIES = 10000
_SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass
class InitializerOptions:
    workdir: str
    skills_dir: str = ""
    max_archive_bytes: int = DEFAULT_MAX_ARCHIVE_BYTES
    max_extracted_bytes: int = DEFAULT_MAX_EXTRACTED_BYTES
    max_archive_entries: int = DEFAULT_MAX_ARCHIVE_ENTRIES
    logger: logging.Logger = logging.getLogger("arkruntime.selfhosted.envinit")


class Initializer:
    def __init__(self, api: Any, options: InitializerOptions) -> None:
        self.api = api
        self.options = options
        if not self.options.skills_dir:
            self.options.skills_dir = str(Path(self.options.workdir) / "skills")

    def setup(self, session: Session) -> None:
        if not session:
            raise ValueError("session must not be empty")
        if not self.options.workdir:
            raise ValueError("workdir must not be empty")
        Path(self.options.workdir).mkdir(parents=True, exist_ok=True)
        Path(self.options.skills_dir).mkdir(parents=True, exist_ok=True)
        for skill in session.skill_refs():
            try:
                self.install_skill(session.id, skill)
            except Exception as exc:  # noqa: BLE001 - one broken skill must not fail session setup.
                # Follow the Go SDK: skill install errors are observable but do
                # not fail the whole session setup.
                self.options.logger.warning(
                    "failed to install skill session_id=%s skill=%s version=%s err=%s",
                    session.id,
                    skill.name_value(),
                    skill.version,
                    exc,
                )
                continue

    def install_skill(self, session_id: str, skill: SkillRef) -> None:
        Path(self.options.workdir).mkdir(parents=True, exist_ok=True)
        Path(self.options.skills_dir).mkdir(parents=True, exist_ok=True)
        resolver = getattr(self.api, "resolve_skill", None)
        if callable(resolver) and skill.id_value().strip():
            skill = resolver(skill)
        name = _safe_skill_dir_name(skill)
        self.options.logger.info(
            "install skill session_id=%s skill=%s version=%s",
            session_id,
            name,
            skill.version,
        )
        try:
            content = self.api.open_skill(session_id, skill)
        except Exception as exc:
            raise RuntimeError(f"download skill {name}: {exc}") from exc
        if content is None or content.body is None:
            raise RuntimeError(f"download skill {name}: empty content")
        try:
            archive_path = self._copy_archive(name, content.body)
        finally:
            if hasattr(content.body, "close"):
                content.body.close()
        tmp = tempfile.mkdtemp(prefix=f".{name}-", dir=self.options.skills_dir)
        try:
            self._extract_archive(archive_path, tmp)
            source = _install_source_dir(Path(tmp))
            target = Path(self.options.skills_dir) / name
            backup = _replace_skill_dir(Path(source), target)
            if backup is not None:
                try:
                    shutil.rmtree(backup)
                except OSError as exc:
                    self.options.logger.warning(
                        "remove old skill backup failed session_id=%s skill=%s path=%s err=%s",
                        session_id,
                        name,
                        backup,
                        exc,
                    )
        finally:
            with suppress(OSError):
                os.remove(archive_path)
            with suppress(OSError):
                if os.path.exists(tmp):
                    shutil.rmtree(tmp)

    def _copy_archive(self, name: str, body: Any) -> str:
        fd, path = tempfile.mkstemp(prefix=f"ark-skill-{name}-")
        copied = 0
        try:
            with os.fdopen(fd, "wb") as out:
                while True:
                    chunk = body.read(65536)
                    if not chunk:
                        break
                    copied += len(chunk)
                    if copied > self.options.max_archive_bytes:
                        raise ValueError(f"skill archive too large: {copied} bytes")
                    out.write(chunk)
            if copied == 0:
                raise ValueError("skill archive is empty")
            return path
        except Exception:
            with suppress(OSError):
                os.remove(path)
            raise

    def _extract_archive(self, archive_path: str, dst: str) -> None:
        with open(archive_path, "rb") as f:
            magic = f.read(4)
        if magic.startswith(b"PK"):
            self._extract_zip(archive_path, dst)
            return
        if magic.startswith(b"\x1f\x8b"):
            self._extract_tar_gz(archive_path, dst)
            return
        raise ValueError("unsupported skill archive format")

    def _extract_zip(self, archive_path: str, dst: str) -> None:
        total = 0
        with zipfile.ZipFile(archive_path) as zf:
            entries = zf.infolist()
            if len(entries) > self.options.max_archive_entries:
                raise ValueError(f"skill archive contains too many entries: {len(entries)}")
            for info in entries:
                target = _safe_join(dst, info.filename)
                if info.is_dir():
                    Path(target).mkdir(parents=True, exist_ok=True)
                    continue
                entry_type = stat.S_IFMT(info.external_attr >> 16)
                if entry_type and not stat.S_ISREG(entry_type):
                    raise ValueError(f"unsupported zip entry type: {info.filename}")
                remaining = self.options.max_extracted_bytes - total
                if remaining < 0 or info.file_size > remaining:
                    raise ValueError(
                        f"skill extracted content too large: more than {self.options.max_extracted_bytes} bytes"
                    )
                Path(target).parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as out:
                    total += _copy_limited(src, out, remaining, self.options.max_extracted_bytes)

    def _extract_tar_gz(self, archive_path: str, dst: str) -> None:
        total = 0
        entries = 0
        with tarfile.open(archive_path, "r:gz") as tf:
            for member in tf:
                entries += 1
                if entries > self.options.max_archive_entries:
                    raise ValueError(f"skill archive contains too many entries: {entries}")
                target = _safe_join(dst, member.name)
                if member.isdir():
                    Path(target).mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    raise ValueError(f"unsupported tar entry type: {member.name}")
                remaining = self.options.max_extracted_bytes - total
                if remaining < 0 or member.size < 0 or member.size > remaining:
                    raise ValueError(
                        f"skill extracted content too large: more than {self.options.max_extracted_bytes} bytes"
                    )
                src = tf.extractfile(member)
                if src is None:
                    continue
                Path(target).parent.mkdir(parents=True, exist_ok=True)
                with src, open(target, "wb") as out:
                    total += _copy_limited(src, out, remaining, self.options.max_extracted_bytes)


def _safe_skill_dir_name(skill: SkillRef) -> str:
    for candidate in (skill.name, skill.display_name, skill.id_value()):
        name = candidate.strip()
        if name and name not in (".", "..") and _SAFE_NAME.match(name):
            return name
    raise ValueError(f"invalid skill name: {skill.name!r}")


def _safe_join(root: str, name: str) -> str:
    if not name or os.path.isabs(name):
        raise ValueError(f"invalid archive path: {name}")
    root_path = Path(root).resolve()
    target = (root_path / name).resolve()
    if target != root_path and root_path not in target.parents:
        raise ValueError(f"archive path escapes skill dir: {name}")
    return str(target)


def _install_source_dir(tmp: Path) -> str:
    entries = list(tmp.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return str(entries[0])
    return str(tmp)


def _replace_skill_dir(source: Path, target: Path) -> Optional[Path]:
    if not os.path.lexists(target):
        os.replace(source, target)
        return None
    backup = Path(tempfile.mkdtemp(prefix=f".{target.name}-backup-", dir=target.parent))
    backup.rmdir()
    os.replace(target, backup)
    try:
        os.replace(source, target)
    except OSError as exc:
        try:
            os.replace(backup, target)
        except OSError as rollback_exc:
            raise OSError(f"replace skill: {exc}; rollback: {rollback_exc}") from exc
        raise
    return backup


def _copy_limited(src: Any, out: Any, limit: int, configured_limit: int) -> int:
    written = 0
    while True:
        chunk = src.read(min(65536, limit - written + 1))
        if not chunk:
            return written
        written += len(chunk)
        if written > limit:
            raise ValueError(f"skill extracted content too large: more than {configured_limit} bytes")
        out.write(chunk)
