# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from arkruntime.selfhosted import Event, FileToolResultStore


def test_recovery_uses_persisted_call_id(tmp_path) -> None:
    store = FileToolResultStore(str(tmp_path))
    store.begin("call-1", Event(id="event-1", type="agent.tool_use", name="bash"))

    pending, _ = store.recover()

    assert pending["call-1"].tool_use_id == "call-1"


def test_recovery_removes_stale_temporary_records(tmp_path) -> None:
    store = FileToolResultStore(str(tmp_path))
    stale = store.dir / ".tool-result-stale.tmp"
    stale.write_text("partial")

    store.recover()

    assert not stale.exists()
