# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import time

import pytest

from arkruntime.selfhosted import (
    APIError,
    EnvironmentWorker,
    EnvironmentWorkerOptions,
    HandleItemOptions,
    HeartbeatResponse,
    Session,
    WorkItem,
    WorkPoller,
    WorkPollerOptions,
)
from arkruntime.selfhosted.types import WorkData, is_fatal_4xx


def _work_item(environment_id: str) -> WorkItem:
    return WorkItem(
        id="work-1",
        created_at="2026-08-24T10:00:00Z",
        environment_id=environment_id,
        data=WorkData(type="session", id="session-1"),
        state="queued",
        type="work",
    )


class _PollAPI:
    def __init__(self, ack_error: BaseException) -> None:
        self.ack_error = ack_error
        self.polls = 0
        self.stops = []

    def poll_work(self, environment_id, **kwargs):
        self.polls += 1
        if self.polls > 1:
            return None
        return _work_item(environment_id)

    def ack_work(self, environment_id, work_id, **kwargs):
        raise self.ack_error

    def stop_work(self, environment_id, work_id, **kwargs):
        self.stops.append((environment_id, work_id, kwargs))


def test_ack_conflict_does_not_stop_unowned_work() -> None:
    api = _PollAPI(APIError(409, "already claimed"))
    poller = WorkPoller(api, WorkPollerOptions(environment_id="env-1", drain=True))

    assert poller.next() is None
    assert poller.error is None
    assert api.stops == []


def test_fatal_ack_error_stops_poller_without_stopping_work() -> None:
    error = APIError(403, "forbidden")
    api = _PollAPI(error)
    poller = WorkPoller(api, WorkPollerOptions(environment_id="env-1", drain=True))

    assert poller.next() is None
    assert poller.error is error
    assert api.stops == []


class _StoppingHeartbeatAPI:
    def __init__(self) -> None:
        self.stops = []

    def heartbeat_work(self, environment_id, work_id, **kwargs):
        return HeartbeatResponse(
            last_heartbeat="2026-08-24T10:00:00Z",
            state="stopping",
            lease_extended=True,
            ttl_seconds=30,
            type="work_heartbeat",
        )

    def get_session(self, session_id):
        return Session(id=session_id)

    def list_events(self, session_id, **kwargs):
        raise AssertionError("runner must observe the heartbeat stop before listing events")

    def stop_work(self, environment_id, work_id, **kwargs):
        self.stops.append((environment_id, work_id, kwargs))


def test_heartbeat_stop_cancels_session_runner(tmp_path) -> None:
    api = _StoppingHeartbeatAPI()
    worker = EnvironmentWorker(
        api,
        EnvironmentWorkerOptions(environment_id="env-1", workdir=str(tmp_path)),
    )

    started = time.monotonic()
    worker.handle_item(HandleItemOptions(work_id="work-1", environment_id="env-1", session_id="session-1"))

    assert time.monotonic() - started < 1
    assert api.stops == [("env-1", "work-1", {"force": True})]


class _LeaseLostHeartbeatAPI(_StoppingHeartbeatAPI):
    def heartbeat_work(self, environment_id, work_id, **kwargs):
        raise APIError(412, "lease lost")


def test_lease_lost_does_not_stop_work(tmp_path) -> None:
    api = _LeaseLostHeartbeatAPI()
    worker = EnvironmentWorker(
        api,
        EnvironmentWorkerOptions(environment_id="env-1", workdir=str(tmp_path)),
    )

    worker.handle_item(HandleItemOptions(work_id="work-1", environment_id="env-1", session_id="session-1"))

    assert api.stops == []


class _ClaimedPollAPI:
    def __init__(self) -> None:
        self.stops = []

    def poll_work(self, environment_id, **kwargs):
        return _work_item(environment_id)

    def ack_work(self, environment_id, work_id, **kwargs):
        return None

    def stop_work(self, environment_id, work_id, **kwargs):
        self.stops.append((environment_id, work_id, kwargs))


@pytest.mark.parametrize("auto_stop, expected_stops", [(True, 1), (False, 0)])
def test_poller_auto_stop_is_configurable(auto_stop, expected_stops) -> None:
    api = _ClaimedPollAPI()
    poller = WorkPoller(api, WorkPollerOptions(environment_id="env-1", auto_stop=auto_stop))

    assert poller.next() is not None
    poller.close()

    assert len(api.stops) == expected_stops


def test_session_id_cannot_escape_worker_root(tmp_path) -> None:
    worker = EnvironmentWorker(object(), EnvironmentWorkerOptions(workdir=str(tmp_path)))

    workdir = worker._workdir_for("../../outside", use_workdir_as_session=False)

    assert str(tmp_path.resolve()) in workdir
    assert ".." not in workdir


@pytest.mark.parametrize("status_code", [408, 409, 412, 429])
def test_recoverable_client_status_is_not_fatal(status_code) -> None:
    assert not is_fatal_4xx(APIError(status_code, "recoverable"))
