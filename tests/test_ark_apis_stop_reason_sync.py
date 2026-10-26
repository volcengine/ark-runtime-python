# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

"""Synced from ark-apis by vendor-session; exercise the real stream decoder."""

import unittest

from arkruntime.types.session import ManagedAgentsStopReason, decode_session_event


class StreamStopReasonTests(unittest.TestCase):
    def test_typed_pending_event_ids(self):
        self.assertIn("event_ids", ManagedAgentsStopReason.model_fields)
        for kind in ("session.status_idle", "session.thread_status_idle"):
            for ids in (["sevt-a", "sevt-b"], ["sevt-b"], []):
                payload = {
                    "type": kind,
                    "id": "sevt-idle",
                    "stop_reason": {"type": "requires_action", "event_ids": ids},
                }
                if kind == "session.thread_status_idle":
                    payload.update(session_thread_id="sthr-1", agent_name="agent")
                with self.subTest(kind=kind, ids=ids):
                    event = decode_session_event(payload)
                    self.assertIsInstance(event.stop_reason, ManagedAgentsStopReason)
                    self.assertEqual(event.stop_reason.event_ids, ids)
                    self.assertEqual(event.stop_reason["event_ids"], ids)
                    self.assertEqual(event.model_dump(exclude_unset=True), payload)

    def test_legacy_and_future_reasons(self):
        for kind in ("end_turn", "retries_exhausted", "future_reason"):
            with self.subTest(kind=kind):
                reason = ManagedAgentsStopReason(type=kind)
                self.assertIsNone(reason.event_ids)
                self.assertEqual(reason.model_dump(exclude_unset=True), {"type": kind})


if __name__ == "__main__":
    unittest.main()
