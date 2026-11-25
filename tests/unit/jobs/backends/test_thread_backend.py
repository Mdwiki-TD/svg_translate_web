"""Tests for ``backends.thread_backend`` and ``backends.thread_cancel_registry``."""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from src.main_app.jobs.backends import thread_cancel_registry as registry
from src.main_app.jobs.backends.thread_backend import ThreadBackend, _runner

MODULE = "src.main_app.jobs.backends.thread_backend"


@pytest.fixture(autouse=True)
def _clean_registry():
    yield
    registry.JOBS_CANCEL_EVENTS.clear()


@pytest.fixture
def mock_executor_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """The backend imports ``JobExecutor`` lazily, so patching the source module is enough."""
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_instance.run.return_value = 0
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr("src.main_app.jobs.job_executor.JobExecutor", _mock_class)
    return _mock_class


def _wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class TestCancelRegistry:
    def test_register_get_and_pop(self) -> None:
        event = threading.Event()

        registry.register_cancel_event(1, event)

        assert registry.get_cancel_event(1) is event
        assert registry.pop_cancel_event(1) is event
        assert registry.get_cancel_event(1) is None

    def test_pop_of_unknown_job_returns_none(self) -> None:
        assert registry.pop_cancel_event(404) is None


class TestStart:
    def test_runs_the_executor_in_a_thread_with_the_user_and_event(
        self,
        flask_app,
        mock_executor_class: MagicMock,
        job_record,
        job_data,
    ) -> None:
        done = threading.Event()
        mock_executor_class.return_value.run.side_effect = lambda *args, **kwargs: done.set() or 0

        with flask_app.app_context():
            name = ThreadBackend().start(job_record, job_data, user={"username": "alice"})

        assert name == "thread-7"
        assert done.wait(5)
        run = mock_executor_class.return_value.run
        assert run.call_args.args == (7,)
        assert run.call_args.kwargs["user"] == {"username": "alice"}
        assert isinstance(run.call_args.kwargs["cancel_event"], threading.Event)
        # signal handlers can only be installed from the main thread
        assert "install_signal_handlers" not in run.call_args.kwargs

    def test_event_is_registered_while_running_and_removed_afterwards(
        self,
        flask_app,
        mock_executor_class: MagicMock,
        job_record,
        job_data,
    ) -> None:
        started, release = threading.Event(), threading.Event()

        def _run(*args, **kwargs):
            started.set()
            release.wait(5)
            return 0

        mock_executor_class.return_value.run.side_effect = _run

        with flask_app.app_context():
            ThreadBackend().start(job_record, job_data)

        assert started.wait(5)
        assert registry.get_cancel_event(7) is not None
        release.set()
        assert _wait_until(lambda: registry.get_cancel_event(7) is None)

    def test_thread_start_failure_unregisters_the_event(
        self,
        flask_app,
        monkeypatch: pytest.MonkeyPatch,
        job_record,
        job_data,
    ) -> None:
        fake_thread_cls = MagicMock()
        fake_thread_cls.return_value.start.side_effect = RuntimeError("cannot start")
        monkeypatch.setattr(
            f"{MODULE}.threading",
            SimpleNamespace(Event=threading.Event, Thread=fake_thread_cls),
        )

        with flask_app.app_context(), pytest.raises(RuntimeError, match="cannot start"):
            ThreadBackend().start(job_record, job_data)

        assert registry.get_cancel_event(7) is None


class TestRunner:
    def test_event_is_removed_even_when_the_executor_raises(
        self,
        flask_app,
        mock_executor_class: MagicMock,
    ) -> None:
        event = threading.Event()
        registry.register_cancel_event(7, event)
        mock_executor_class.return_value.run.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            _runner(7, {"username": "alice"}, event, flask_app)

        assert registry.get_cancel_event(7) is None


class TestCancel:
    def test_sets_the_registered_event(self, job_record) -> None:
        event = threading.Event()
        registry.register_cancel_event(7, event)

        assert ThreadBackend().cancel(job_record) is True
        assert event.is_set()

    def test_returns_false_when_the_job_runs_in_another_process(self, make_job_record) -> None:
        assert ThreadBackend().cancel(make_job_record(id=999)) is False
