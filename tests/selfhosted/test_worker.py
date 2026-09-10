# Copyright (c) 2026 ByteDance Ltd. and/or its affiliates.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
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
from arkruntime.selfhosted.tools import ToolContext
from arkruntime.selfhosted.types import WorkData, is_fatal_4xx
from arkruntime.selfhosted.worker import default_worker_id


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


def test_ack_conflict_retries_without_stopping_work(monkeypatch) -> None:
    api = _PollAPI(APIError(409, "already claimed"))
    poller = WorkPoller(api, WorkPollerOptions(environment_id="env-1", drain=True))
    sleeps = []
    monkeypatch.setattr(poller, "_sleep", sleeps.append)
    monkeypatch.setattr("arkruntime.selfhosted.worker.random.random", lambda: 0.5)

    assert poller.next() is None
    assert poller.error is None
    assert api.stops == []
    assert sleeps == [2.5]


def test_fatal_ack_error_force_stops_work_and_continues() -> None:
    error = APIError(403, "forbidden")
    api = _PollAPI(error)
    poller = WorkPoller(api, WorkPollerOptions(environment_id="env-1", drain=True))

    assert poller.next() is None
    assert poller.error is None
    assert api.stops == [("env-1", "work-1", {"force": True})]


def test_poller_does_not_swallow_programming_errors() -> None:
    class BrokenAPI:
        def poll_work(self, environment_id, **kwargs):
            raise ValueError("broken adapter")

    poller = WorkPoller(BrokenAPI(), WorkPollerOptions(environment_id="env-1"))

    with pytest.raises(ValueError, match="broken adapter"):
        poller.next()


def test_default_worker_id_is_unique_per_worker() -> None:
    first = default_worker_id()
    second = default_worker_id()

    assert first != second
    assert first.rsplit("-", 1)[0] == second.rsplit("-", 1)[0]
    assert len(first.rsplit("-", 1)[1]) == 12


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


def test_worker_tool_timeout_overrides_tool_context(tmp_path) -> None:
    worker = EnvironmentWorker(
        object(),
        EnvironmentWorkerOptions(
            workdir=str(tmp_path),
            tool_timeout_seconds=0.02,
        ),
    )

    context = worker._tool_context(str(tmp_path), None)

    assert context.tool_timeout_seconds == 0.02


@pytest.mark.parametrize("timeout", [None, 0, -1])
def test_worker_nonpositive_tool_timeout_preserves_tool_context(tmp_path, timeout) -> None:
    worker = EnvironmentWorker(
        object(),
        EnvironmentWorkerOptions(
            workdir=str(tmp_path),
            tool_context=ToolContext(workdir=str(tmp_path), tool_timeout_seconds=7),
            tool_timeout_seconds=timeout,
        ),
    )

    context = worker._tool_context(str(tmp_path), None)

    assert context.tool_timeout_seconds == 7


def test_worker_options_preserve_legacy_positional_order() -> None:
    custom_tools = {"custom": object()}
    logger = logging.getLogger("legacy-positional-worker")

    options = EnvironmentWorkerOptions("env-1", "worker-1", ".", False, None, None, 60, custom_tools, logger)

    assert options.custom_tools is custom_tools
    assert options.logger is logger
    assert options.tool_timeout_seconds is None


def test_worker_uses_configured_workdir(tmp_path) -> None:
    worker = EnvironmentWorker(object(), EnvironmentWorkerOptions(workdir=str(tmp_path)))

    workdir = worker._workdir()

    assert workdir == str(tmp_path.resolve())


@pytest.mark.parametrize("status_code", [408, 409, 412, 429])
def test_recoverable_client_status_is_not_fatal(status_code) -> None:
    assert not is_fatal_4xx(APIError(status_code, "recoverable"))
