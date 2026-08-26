# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import io
import logging
import os
import zipfile

from arkruntime.selfhosted import Initializer, InitializerOptions, Session, SkillRef
from arkruntime.selfhosted.envinit import _replace_skill_dir
from arkruntime.selfhosted.types import SkillContent


class FailingSkillAPI:
    def open_skill(self, session_id: str, skill: SkillRef) -> None:
        raise RuntimeError("content endpoint unavailable")


class ResolvingSkillAPI:
    def __init__(self, archive: bytes) -> None:
        self.archive = archive

    def resolve_skill(self, skill: SkillRef) -> SkillRef:
        return SkillRef(
            name="canonical-skill-name",
            skill_id=skill.id_value(),
            type=skill.type,
            version=skill.version,
        )

    def open_skill(self, session_id: str, skill: SkillRef) -> SkillContent:
        return SkillContent(body=io.BytesIO(self.archive), content_length=len(self.archive))


class _CloseTrackingBody(io.BytesIO):
    was_closed = False

    def close(self) -> None:
        self.was_closed = True
        super().close()


def test_setup_logs_skill_download_failure_and_continues(tmp_path, caplog) -> None:
    logger = logging.getLogger("test.selfhosted.envinit")
    session = Session.from_mapping(
        {
            "id": "session-1",
            "skills": [
                {
                    "type": "skill_hub",
                    "skill_id": "skill-1",
                    "display_name": "demo",
                    "version": "2",
                }
            ],
        }
    )
    initializer = Initializer(
        FailingSkillAPI(),
        InitializerOptions(workdir=str(tmp_path), logger=logger),
    )

    with caplog.at_level(logging.WARNING, logger=logger.name):
        initializer.setup(session)

    assert "failed to install skill" in caplog.text
    assert "session_id=session-1" in caplog.text
    assert "skill=demo" in caplog.text
    assert "version=2" in caplog.text
    assert "download skill demo: content endpoint unavailable" in caplog.text


def test_setup_installs_skill_under_resolved_metadata_name(tmp_path) -> None:
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("SKILL.md", "hello")
    session = Session.from_mapping(
        {
            "id": "session-1",
            "skills": [{"type": "custom", "skill_id": "skill-1", "version": "1"}],
        }
    )
    initializer = Initializer(
        ResolvingSkillAPI(archive.getvalue()),
        InitializerOptions(workdir=str(tmp_path)),
    )

    initializer.setup(session)

    assert (tmp_path / "skills" / "canonical-skill-name" / "SKILL.md").read_text() == "hello"
    assert not (tmp_path / "skills" / "skill-1").exists()


def test_install_closes_skill_body_when_archive_copy_fails(tmp_path) -> None:
    body = _CloseTrackingBody(b"archive-too-large")
    api = ResolvingSkillAPI(b"")
    api.open_skill = lambda session_id, skill: SkillContent(body=body, content_length=17)
    initializer = Initializer(
        api,
        InitializerOptions(workdir=str(tmp_path), max_archive_bytes=1),
    )

    try:
        initializer.install_skill("session-1", SkillRef(skill_id="skill-1", version="1"))
    except ValueError as exc:
        assert "archive too large" in str(exc)
    else:
        raise AssertionError("expected archive size failure")

    assert body.was_closed


def test_zip_archive_entry_limit_is_enforced(tmp_path) -> None:
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("one", "1")
        output.writestr("two", "2")
    initializer = Initializer(
        ResolvingSkillAPI(archive.getvalue()),
        InitializerOptions(workdir=str(tmp_path), max_archive_entries=1),
    )

    try:
        initializer.install_skill("session-1", SkillRef(skill_id="skill-1", version="1"))
    except ValueError as exc:
        assert "too many entries" in str(exc)
    else:
        raise AssertionError("expected archive entry limit failure")


def test_replace_skill_rolls_back_old_version_when_commit_fails(tmp_path, monkeypatch) -> None:
    source = tmp_path / "new-skill"
    target = tmp_path / "installed-skill"
    source.mkdir()
    target.mkdir()
    (source / "marker.txt").write_text("new")
    (target / "marker.txt").write_text("old")
    real_replace = os.replace

    def fail_new_commit(from_path, to_path):
        if os.fspath(from_path) == os.fspath(source) and os.fspath(to_path) == os.fspath(target):
            raise OSError("commit failed")
        real_replace(from_path, to_path)

    monkeypatch.setattr("arkruntime.selfhosted.envinit.os.replace", fail_new_commit)

    try:
        _replace_skill_dir(source, target)
    except OSError as exc:
        assert "commit failed" in str(exc)
    else:
        raise AssertionError("expected skill commit failure")

    assert (target / "marker.txt").read_text() == "old"
    assert (source / "marker.txt").read_text() == "new"
