# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from arkruntime.selfhosted import Event, FileToolResultStore


def test_recovery_uses_persisted_call_id(tmp_path) -> None:
    store = FileToolResultStore(str(tmp_path))
    assert store.dir == tmp_path / ".ma_self_hosted_worker" / "tool_ledger"
    store.begin("call-1", Event(id="event-1", type="agent.tool_use", name="bash"))

    pending, _ = store.recover()

    assert pending["call-1"].tool_use_id == "call-1"


def test_recovery_removes_stale_temporary_records(tmp_path) -> None:
    store = FileToolResultStore(str(tmp_path))
    stale = store.dir / ".tool-result-stale.tmp"
    stale.write_text("partial")

    store.recover()

    assert not stale.exists()


def test_session_store_isolates_sessions(tmp_path) -> None:
    first = FileToolResultStore(str(tmp_path), "session-a")
    second = FileToolResultStore(str(tmp_path), "session-b")
    assert first.dir == tmp_path / ".ma_self_hosted_worker" / "tool_ledger" / "session-a"

    first.begin("call-1", Event(id="event-1", type="agent.tool_use", name="bash"))

    assert second.recover() == ({}, {})


def test_session_store_sanitizes_session_id(tmp_path) -> None:
    store = FileToolResultStore(str(tmp_path), "../../outside")
    base = tmp_path / ".ma_self_hosted_worker" / "tool_ledger"

    assert store.dir.parent == base
    assert store.dir.name.startswith("session-")


def test_discard_removes_recovered_record(tmp_path) -> None:
    store = FileToolResultStore(str(tmp_path), "session-a")
    store.begin("call-1", Event(id="call-1", type="agent.tool_use", name="bash"))

    store.discard("call-1")

    assert store.recover() == ({}, {})
