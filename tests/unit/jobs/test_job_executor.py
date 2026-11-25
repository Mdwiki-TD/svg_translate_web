"""Tests for ``jobs.job_executor.JobExecutor``."""

from __future__ import annotations

import signal
import threading
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from src.main_app.jobs.job_executor import (
    EXIT_AUTH_ERROR,
    EXIT_CONFIG_ERROR,
    EXIT_CRASHED,
    EXIT_OK,
    JobExecutor,
)

MODULE = "src.main_app.jobs.job_executor"
_UNSET = object()


@pytest.fixture
def mock_load_job_data(monkeypatch: pytest.MonkeyPatch, job_data: Any) -> MagicMock:
    _mock = MagicMock(side_effect=lambda job_type: job_data if job_type == job_data.job_type else None)
    monkeypatch.setattr(f"{MODULE}.load_job_data", _mock)
    return _mock


@pytest.fixture
def mock_build_job_user(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock(side_effect=lambda username: {"username": username, "access_token": "t"})
    monkeypatch.setattr(f"{MODULE}.build_job_user", _mock)
    return _mock


@pytest.fixture
def mock_signal(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(f"{MODULE}.signal.signal", _mock)
    return _mock


@pytest.fixture
def make_jobs_service(make_job_record: Callable[..., SimpleNamespace]) -> Callable[..., MagicMock]:
    """Service whose first ``get_by`` returns the job and the second returns it in ``then`` status.

    ``first=None`` simulates a missing job.
    """

    def _factory(first: Any = _UNSET, then: str = "completed") -> MagicMock:
        svc = MagicMock()
        if first is None:
            svc.get_by.return_value = None
        else:
            initial = make_job_record() if first is _UNSET else first
            svc.get_by.side_effect = [initial, make_job_record(status=then)]
        return svc

    return _factory


pytestmark = pytest.mark.usefixtures("mock_load_job_data", "mock_build_job_user")


class TestEarlyExits:
    def test_job_not_found(self, make_jobs_service: Callable[..., MagicMock]) -> None:
        svc = make_jobs_service(first=None)

        assert JobExecutor(svc).run(7) == EXIT_CONFIG_ERROR

    def test_cancelled_before_start_does_nothing(
        self,
        make_jobs_service: Callable[..., MagicMock],
        make_job_record: Callable[..., SimpleNamespace],
        fake_worker_cls: type,
    ) -> None:
        svc = make_jobs_service(first=make_job_record(status="cancelled"))

        assert JobExecutor(svc).run(7) == EXIT_OK
        assert fake_worker_cls.instances == []

    def test_unknown_job_type_is_marked_failed(
        self,
        make_jobs_service: Callable[..., MagicMock],
        make_job_record: Callable[..., SimpleNamespace],
    ) -> None:
        job = make_job_record(job_type="nope")
        svc = make_jobs_service(first=job)

        assert JobExecutor(svc).run(7) == EXIT_CONFIG_ERROR
        svc.mark_failed.assert_called_once_with(job, "unknown job type nope")

    def test_user_without_token_is_marked_failed(
        self,
        make_jobs_service: Callable[..., MagicMock],
        mock_build_job_user: MagicMock,
        fake_worker_cls: type,
    ) -> None:
        mock_build_job_user.side_effect = None
        mock_build_job_user.return_value = None
        svc = make_jobs_service()

        assert JobExecutor(svc).run(7) == EXIT_AUTH_ERROR
        svc.mark_failed.assert_called_once()
        assert fake_worker_cls.instances == []


class TestRun:
    def test_builds_the_runner_with_every_field(
        self,
        make_jobs_service: Callable[..., MagicMock],
        fake_worker_cls: type,
    ) -> None:
        svc = make_jobs_service()

        assert JobExecutor(svc).run(7) == EXIT_OK

        runner = fake_worker_cls.instances[0].runner
        assert runner.job_id == 7
        assert runner.job_type == "demo"
        assert runner.args == {"a": 1}
        assert runner.form_data == {"f": 2}
        assert runner.job_for_admin is True
        assert runner.user == {"username": "alice", "access_token": "t"}

    def test_does_not_duplicate_the_workers_running_status_update(
        self,
        make_jobs_service: Callable[..., MagicMock],
    ) -> None:
        svc = make_jobs_service()

        JobExecutor(svc).run(7)

        svc.update_job_status.assert_not_called()
        svc.mark_as_completed.assert_not_called()

    def test_missing_payload_gives_empty_args(
        self,
        make_jobs_service: Callable[..., MagicMock],
        make_job_record: Callable[..., SimpleNamespace],
        fake_worker_cls: type,
    ) -> None:
        svc = make_jobs_service(first=make_job_record(payload=None))

        JobExecutor(svc).run(7)

        runner = fake_worker_cls.instances[0].runner
        assert runner.args == {}
        assert runner.form_data is None

    @pytest.mark.parametrize("left_status", ["pending", "running"])
    def test_safety_net_completes_a_job_the_worker_left_open(
        self,
        make_jobs_service: Callable[..., MagicMock],
        left_status: str,
    ) -> None:
        svc = make_jobs_service(then=left_status)

        assert JobExecutor(svc).run(7) == EXIT_OK
        svc.mark_as_completed.assert_called_once()

    def test_explicit_user_skips_the_db_lookup(
        self,
        make_jobs_service: Callable[..., MagicMock],
        mock_build_job_user: MagicMock,
        fake_worker_cls: type,
    ) -> None:
        svc = make_jobs_service()

        JobExecutor(svc).run(7, user={"username": "Background job"})

        mock_build_job_user.assert_not_called()
        assert fake_worker_cls.instances[0].runner.user == {"username": "Background job"}

    def test_passes_the_given_cancel_event(
        self,
        make_jobs_service: Callable[..., MagicMock],
        fake_worker_cls: type,
    ) -> None:
        svc = make_jobs_service()
        event = threading.Event()

        JobExecutor(svc).run(7, cancel_event=event)

        assert fake_worker_cls.instances[0].runner.cancel_event is event

    def test_creates_a_cancel_event_when_none_is_given(
        self,
        make_jobs_service: Callable[..., MagicMock],
        fake_worker_cls: type,
    ) -> None:
        svc = make_jobs_service()

        JobExecutor(svc).run(7)

        assert isinstance(fake_worker_cls.instances[0].runner.cancel_event, threading.Event)


class TestFailures:
    @pytest.mark.parametrize("behaviour", ["run_error", "ctor_error"])
    def test_worker_errors_mark_the_job_failed(
        self,
        make_jobs_service: Callable[..., MagicMock],
        fake_worker_cls: type,
        behaviour: str,
    ) -> None:
        fake_worker_cls.behaviour = behaviour
        svc = make_jobs_service()

        assert JobExecutor(svc).run(7) == EXIT_CRASHED
        assert svc.mark_failed.call_args.args[1] == "unhandled exception"
        svc.mark_as_completed.assert_not_called()


class TestSignalHandlers:
    def test_not_installed_by_default_so_it_can_run_in_a_thread(
        self,
        make_jobs_service: Callable[..., MagicMock],
        mock_signal: MagicMock,
    ) -> None:
        svc = make_jobs_service()
        results: list[int] = []

        thread = threading.Thread(target=lambda: results.append(JobExecutor(svc).run(7)))
        thread.start()
        thread.join(5)

        assert results == [EXIT_OK]
        mock_signal.assert_not_called()

    def test_sigterm_sets_the_cancel_event_when_enabled(
        self,
        make_jobs_service: Callable[..., MagicMock],
        mock_signal: MagicMock,
    ) -> None:
        svc = make_jobs_service()
        event = threading.Event()

        JobExecutor(svc).run(7, cancel_event=event, install_signal_handlers=True)

        mock_signal.assert_called_once()
        signum, handler = mock_signal.call_args.args
        assert signum == signal.SIGTERM
        assert not event.is_set()
        handler(signal.SIGTERM, None)
        assert event.is_set()
