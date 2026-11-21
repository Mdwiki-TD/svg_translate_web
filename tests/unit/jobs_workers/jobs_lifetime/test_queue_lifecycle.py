"""Lifecycle tests for the job queue: cancellation, backend hooks, recovery."""

from __future__ import annotations

import threading
from typing import Any
from unittest.mock import MagicMock

import pytest
from src.main_app.database.services import JobsService
from src.main_app.jobs_workers.backends.thread_backend import _runner
from src.main_app.jobs_workers.jobs_lifetime import cancel_registry, jobs_starter
from src.main_app.jobs_workers.jobs_lifetime.cancel_registry import (
    get_cancel_event,
    pop_cancel_event,
    register_cancel_event,
)
from src.main_app.jobs_workers.jobs_lifetime.jobs_canceller import JobCanceller
from src.main_app.jobs_workers.jobs_lifetime.jobs_queue import JobIdentityResolver, JobsQueue
from src.main_app.jobs_workers.objects import JobData, JobsRunner

JOB_TYPE = "lifecycle_test_job"
OTHER_JOB_TYPE = "lifecycle_test_other"


class FakeWorker:
    JOB_TYPE = JOB_TYPE

    def __init__(self, data: Any = None) -> None:
        self.data = data

    def run(self) -> None:
        return None


class RecordingBackend:
    def __init__(self) -> None:
        self.started: list[int] = []

    def start(self, job: Any, job_data: JobData, payload: dict[str, Any]) -> str:
        self.started.append(job.id)
        return f"fake-{job.id}"

    def cancel(self, job: Any) -> bool:
        return True


@pytest.fixture(autouse=True)
def register_job_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        jobs_starter,
        "jobs_data_admins",
        {
            JOB_TYPE: JobData(job_type=JOB_TYPE, job_name="Lifecycle", job_class=FakeWorker),
            OTHER_JOB_TYPE: JobData(job_type=OTHER_JOB_TYPE, job_name="Lifecycle Other", job_class=FakeWorker),
        },
    )
    monkeypatch.setattr(jobs_starter, "jobs_data_public", {})
    monkeypatch.setattr(
        JobIdentityResolver,
        "resolve",
        lambda self, username: {"username": username, "access_token": b"e", "access_secret": b"e"},
    )


@pytest.fixture
def backend() -> RecordingBackend:
    return RecordingBackend()


@pytest.fixture
def queue(backend: RecordingBackend) -> JobsQueue:
    return JobsQueue(backend=backend)


@pytest.fixture
def jobs_service() -> JobsService:
    return JobsService()


@pytest.fixture(autouse=True)
def clean_cancel_events():
    """Clear the cancel-event registry around each test."""
    with cancel_registry.JOBS_CANCEL_EVENTS_LOCK:
        cancel_registry.JOBS_CANCEL_EVENTS.clear()
    yield
    with cancel_registry.JOBS_CANCEL_EVENTS_LOCK:
        cancel_registry.JOBS_CANCEL_EVENTS.clear()


class TestPendingCancellation:
    def test_cancel_pending_job_never_touches_backend(
        self, queue: JobsQueue, backend: RecordingBackend, jobs_service: JobsService, monkeypatch
    ) -> None:
        queue.enqueue(JOB_TYPE, "user")
        queued = queue.enqueue(JOB_TYPE, "user")

        cancel_spy = MagicMock(wraps=backend.cancel)
        monkeypatch.setattr(backend, "cancel", cancel_spy)
        create_cancel_file = MagicMock()
        monkeypatch.setattr(
            "src.main_app.jobs_workers.jobs_lifetime.jobs_canceller.JobFilesService.create_cancel_file",
            create_cancel_file,
        )

        assert JobCanceller(jobs_queue=queue).cancel(queued.job_id, JOB_TYPE) is True

        cancel_spy.assert_not_called()
        create_cancel_file.assert_not_called()
        assert backend.started == [1]

        job = jobs_service.get_job(queued.job_id, JOB_TYPE)
        assert job.status == "cancelled"
        assert job.is_running is None

    def test_cancelled_pending_job_is_never_dispatched(
        self, queue: JobsQueue, backend: RecordingBackend, jobs_service: JobsService
    ) -> None:
        first = queue.enqueue(JOB_TYPE, "user")
        second = queue.enqueue(JOB_TYPE, "user")
        third = queue.enqueue(JOB_TYPE, "user")

        JobCanceller(jobs_queue=queue).cancel(second.job_id, JOB_TYPE)
        jobs_service.update_job_status(first.job_id, "completed", job_type=JOB_TYPE)

        assert queue.dispatch_next(JOB_TYPE) == third.job_id
        assert backend.started == [first.job_id, third.job_id]

    def test_queue_positions_update_after_cancel(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        queue.enqueue(JOB_TYPE, "user")
        second = queue.enqueue(JOB_TYPE, "user")
        third = queue.enqueue(JOB_TYPE, "user")

        assert jobs_service.get_queue_position(third.job_id) == 2

        queue.cancel_pending(second.job_id, JOB_TYPE)

        assert jobs_service.get_queue_position(third.job_id) == 1
        assert jobs_service.get_queue_position(second.job_id) == 0


class TestRunningCancellation:
    def test_running_job_slot_not_released_on_cancel_request(
        self, queue: JobsQueue, backend: RecordingBackend, jobs_service: JobsService
    ) -> None:
        running = queue.enqueue(JOB_TYPE, "user")
        queued = queue.enqueue(JOB_TYPE, "user")
        register_cancel_event(running.job_id, threading.Event())

        assert JobCanceller(jobs_queue=queue).cancel(running.job_id, JOB_TYPE) is True

        # Cancellation was requested but the execution may still be winding down
        assert get_cancel_event(running.job_id) is not None
        assert jobs_service.has_running_job(JOB_TYPE) is True
        assert backend.started == [running.job_id]
        assert jobs_service.get_job(queued.job_id, JOB_TYPE).status == "pending"

        pop_cancel_event(running.job_id)

    def test_next_job_starts_only_after_execution_stopped(
        self, queue: JobsQueue, backend: RecordingBackend, jobs_service: JobsService
    ) -> None:
        running = queue.enqueue(JOB_TYPE, "user")
        queued = queue.enqueue(JOB_TYPE, "user")

        jobs_service.cancel_job_db(running.job_id, JOB_TYPE)
        assert queue.dispatch_next(JOB_TYPE) is None

        # Worker reached its terminal state -> slot released
        jobs_service.update_job_status(running.job_id, "cancelled", job_type=JOB_TYPE)
        assert queue.dispatch_next(JOB_TYPE) == queued.job_id
        assert backend.started == [running.job_id, queued.job_id]


class TestBackendFinishHook:
    def test_runner_dispatches_next_queued_job(
        self, queue: JobsQueue, backend: RecordingBackend, jobs_service: JobsService, monkeypatch
    ) -> None:
        first = queue.enqueue(JOB_TYPE, "user")
        second = queue.enqueue(JOB_TYPE, "user")

        # The worker marks its own terminal state, releasing the active slot
        jobs_service.update_job_status(first.job_id, "completed", job_type=JOB_TYPE)

        dispatch_spy = MagicMock(wraps=queue.dispatch_next)
        monkeypatch.setattr("src.main_app.jobs_workers.jobs_lifetime.jobs_queue.JobsQueue.dispatch_next", dispatch_spy)

        flask_app = MagicMock()
        runner_data = JobsRunner(job_id=first.job_id, user={"username": "user"}, job_type=JOB_TYPE)
        register_cancel_event(first.job_id, threading.Event())

        _runner(runner_data, lambda data: FakeWorker(data), flask_app)

        assert get_cancel_event(first.job_id) is None
        dispatch_spy.assert_called_once_with(JOB_TYPE)
        assert second.job_id > 0

    def test_runner_without_job_type_does_not_dispatch(self, monkeypatch) -> None:
        dispatch_spy = MagicMock()
        monkeypatch.setattr(
            "src.main_app.jobs_workers.jobs_lifetime.jobs_queue.JobsQueue.on_job_finished", dispatch_spy
        )

        flask_app = MagicMock()
        runner_data = JobsRunner(job_id=1, user={"username": "user"})
        _runner(runner_data, lambda data: FakeWorker(data), flask_app)

        dispatch_spy.assert_not_called()


class TestStartupRecovery:
    def test_recover_starts_pending_jobs_left_by_previous_process(
        self, queue: JobsQueue, backend: RecordingBackend, jobs_service: JobsService
    ) -> None:
        # A pending job persisted before a restart, no active job of its type
        pending = jobs_service.enqueue_job(JOB_TYPE, "user")
        queue.files_service.save_payload(pending.id, JOB_TYPE, {"args": {}, "form_data": None, "username": "user"})

        dispatched = queue.recover(force=True)

        assert dispatched == [pending.id]
        assert backend.started == [pending.id]
        assert jobs_service.get_job(pending.id, JOB_TYPE).status == "running"

    def test_recover_does_not_touch_running_jobs(
        self, queue: JobsQueue, backend: RecordingBackend, jobs_service: JobsService
    ) -> None:
        running = queue.enqueue(JOB_TYPE, "user")

        dispatched = queue.recover(force=True)

        assert dispatched == []
        assert backend.started == [running.job_id]
        assert jobs_service.get_job(running.job_id, JOB_TYPE).status == "running"

    def test_recover_is_throttled(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        pending = jobs_service.enqueue_job(JOB_TYPE, "user")
        queue.files_service.save_payload(pending.id, JOB_TYPE, {"args": {}, "form_data": None, "username": "user"})

        assert queue.recover(force=True) == [pending.id]

        other = jobs_service.enqueue_job(OTHER_JOB_TYPE, "user")
        queue.files_service.save_payload(other.id, OTHER_JOB_TYPE, {"args": {}, "form_data": None, "username": "user"})

        # Throttled: nothing happens within the interval
        assert queue.recover(min_interval=3600) == []
        # Forced: the pending job is dispatched
        assert queue.recover(force=True) == [other.id]
