"""Unit tests for the database backed job queue (JobsQueue).

These tests use the real sqlite database provided by the shared ``setup_db``
fixture and a fake backend, so they assert observable queue behavior and the
resulting database state.
"""

from __future__ import annotations

from typing import Any

import pytest
from src.main_app.database.models import JobRecord
from src.main_app.database.services import JobsService
from src.main_app.jobs_workers.jobs_lifetime import jobs_starter
from src.main_app.jobs_workers.jobs_lifetime.jobs_queue import (
    EnqueueResult,
    JobCredentialsError,
    JobIdentityResolver,
    JobsQueue,
    sanitize_payload,
)
from src.main_app.jobs_workers.objects import JobData

QUEUE_JOB_TYPE = "queue_test_job"
OTHER_JOB_TYPE = "queue_test_other"


class FakeWorker:
    """Stand-in job class; never executed in these tests."""

    JOB_TYPE = QUEUE_JOB_TYPE

    def __init__(self, data: Any = None) -> None:
        self.data = data

    def run(self) -> None:  # pragma: no cover - not executed here
        return None


class FakeBackend:
    """Records backend submissions instead of spawning threads."""

    def __init__(self, fail_for: set[int] | None = None) -> None:
        self.started: list[tuple[int, dict[str, Any]]] = []
        self.fail_for = fail_for or set()

    def start(self, job: JobRecord, job_data: JobData, payload: dict[str, Any]) -> str:
        if job.id in self.fail_for:
            raise RuntimeError("backend exploded")
        self.started.append((job.id, payload))
        return f"fake-{job.id}"

    def cancel(self, job: JobRecord) -> bool:
        return True

    @property
    def started_ids(self) -> list[int]:
        return [job_id for job_id, _ in self.started]


@pytest.fixture(autouse=True)
def register_queue_job_types(monkeypatch: pytest.MonkeyPatch) -> dict[str, JobData]:
    """Register the job types used by these tests."""
    jobs_data = {
        QUEUE_JOB_TYPE: JobData(
            job_type=QUEUE_JOB_TYPE,
            job_name="Queue Test Job",
            job_class=FakeWorker,
        ),
        OTHER_JOB_TYPE: JobData(
            job_type=OTHER_JOB_TYPE,
            job_name="Queue Test Other",
            job_class=FakeWorker,
        ),
    }
    monkeypatch.setattr(jobs_starter, "jobs_data_admins", jobs_data)
    monkeypatch.setattr(jobs_starter, "jobs_data_public", {})
    return jobs_data


@pytest.fixture
def fake_backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def queue(fake_backend: FakeBackend, monkeypatch: pytest.MonkeyPatch) -> JobsQueue:
    """A queue with a fake backend and credentials that always resolve."""
    monkeypatch.setattr(
        JobIdentityResolver,
        "resolve",
        lambda self, username: {"username": username, "access_token": b"enc", "access_secret": b"enc"},
    )
    return JobsQueue(backend=fake_backend)


@pytest.fixture
def jobs_service() -> JobsService:
    return JobsService()


class TestEnqueue:
    def test_three_jobs_of_same_type_are_all_accepted(self, queue: JobsQueue, fake_backend: FakeBackend) -> None:
        results = [queue.enqueue(QUEUE_JOB_TYPE, "user") for _ in range(3)]

        assert all(isinstance(result, EnqueueResult) for result in results)
        assert len({result.job_id for result in results}) == 3
        # Only the first job is handed to the backend
        assert len(fake_backend.started_ids) == 1
        assert fake_backend.started_ids[0] == results[0].job_id

    def test_first_job_starts_immediately(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        result = queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert result.queued is False
        assert result.started is True
        assert result.position == 0

        job = jobs_service.get_job(result.job_id, QUEUE_JOB_TYPE)
        assert job.status == "running"
        assert job.is_running == 1

    def test_second_job_is_queued_with_position(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        queue.enqueue(QUEUE_JOB_TYPE, "user")
        second = queue.enqueue(QUEUE_JOB_TYPE, "user")
        third = queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert second.queued is True
        assert second.position == 1
        assert third.position == 2

        queued = jobs_service.get_job(second.job_id, QUEUE_JOB_TYPE)
        assert queued.status == "pending"
        assert queued.is_running is None

    def test_payload_is_persisted_without_secrets(self, queue: JobsQueue) -> None:
        result = queue.enqueue(
            QUEUE_JOB_TYPE,
            "user",
            args={"csrf_token": "secret", "keep": "1"},
            form_data={"csrf_token": "secret", "title": "File:A.svg"},
        )

        stored = queue.files_service.load_payload(result.job_id, QUEUE_JOB_TYPE)

        assert stored is not None
        assert stored["args"] == {"keep": "1"}
        assert stored["form_data"] == {"title": "File:A.svg"}
        assert stored["username"] == "user"
        assert "access_token" not in stored

    def test_unknown_job_type_raises(self, queue: JobsQueue) -> None:
        with pytest.raises(ValueError, match="Unknown job type"):
            queue.enqueue("nope", "user")

    def test_missing_username_raises(self, queue: JobsQueue) -> None:
        with pytest.raises(ValueError, match="User authentication data is required"):
            queue.enqueue(QUEUE_JOB_TYPE, "")

    def test_payload_persistence_failure_does_not_dispatch(
        self, fake_backend: FakeBackend, monkeypatch: pytest.MonkeyPatch, jobs_service: JobsService
    ) -> None:
        from src.main_app.io.jobs_files_service import JobFilesService

        def _boom(self, job_id: int, job_type: str, payload: dict[str, Any]) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(JobFilesService, "save_payload", _boom)
        queue = JobsQueue(backend=fake_backend)

        with pytest.raises(RuntimeError, match="Failed to store the payload"):
            queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert fake_backend.started_ids == []
        # The incomplete job is failed, never left as a phantom queue entry
        jobs = jobs_service.list_jobs(job_type=QUEUE_JOB_TYPE)
        assert len(jobs) == 1
        assert jobs[0].status == "failed"
        assert jobs[0].is_running is None


class TestFifoOrdering:
    def test_jobs_run_in_fifo_order(self, queue: JobsQueue, fake_backend: FakeBackend, jobs_service) -> None:
        first = queue.enqueue(QUEUE_JOB_TYPE, "user")
        second = queue.enqueue(QUEUE_JOB_TYPE, "user")
        third = queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert fake_backend.started_ids == [first.job_id]

        jobs_service.update_job_status(first.job_id, "completed", job_type=QUEUE_JOB_TYPE)
        queue.dispatch_next(QUEUE_JOB_TYPE)
        assert fake_backend.started_ids == [first.job_id, second.job_id]

        jobs_service.update_job_status(second.job_id, "completed", job_type=QUEUE_JOB_TYPE)
        queue.dispatch_next(QUEUE_JOB_TYPE)
        assert fake_backend.started_ids == [first.job_id, second.job_id, third.job_id]

    def test_next_pending_uses_created_at_then_id(self, queue: JobsQueue) -> None:
        first = queue.enqueue(QUEUE_JOB_TYPE, "user")
        second = queue.enqueue(QUEUE_JOB_TYPE, "user")

        nxt = queue.get_next_pending(QUEUE_JOB_TYPE)

        assert nxt is not None
        # The first job is running, so the oldest pending one is the second
        assert nxt.id == second.job_id
        assert first.job_id != second.job_id

    def test_different_job_types_run_concurrently(self, queue: JobsQueue, fake_backend: FakeBackend) -> None:
        first = queue.enqueue(QUEUE_JOB_TYPE, "user")
        other = queue.enqueue(OTHER_JOB_TYPE, "user")

        assert sorted(fake_backend.started_ids) == sorted([first.job_id, other.job_id])

    def test_queue_positions_are_per_job_type(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        queue.enqueue(QUEUE_JOB_TYPE, "user")
        queued_a = queue.enqueue(QUEUE_JOB_TYPE, "user")
        queue.enqueue(OTHER_JOB_TYPE, "user")
        queued_b = queue.enqueue(OTHER_JOB_TYPE, "user")

        positions = queue.queue_positions(QUEUE_JOB_TYPE)

        assert positions == {queued_a.job_id: 1}
        assert queue.queue_position(queued_b.job_id) == 1
        assert jobs_service.get_queue_positions(OTHER_JOB_TYPE) == {queued_b.job_id: 1}


class TestClaiming:
    def test_claim_is_atomic_and_single_winner(self, queue: JobsService, jobs_service: JobsService) -> None:
        jobs_queue = queue
        jobs_queue.enqueue(QUEUE_JOB_TYPE, "user")
        pending = jobs_queue.enqueue(QUEUE_JOB_TYPE, "user")

        # Simulate a second dispatcher claiming the same pending job
        assert jobs_service.claim_pending_job(pending.job_id) is False

    def test_unique_constraint_prevents_second_active_job(self, jobs_service: JobsService) -> None:
        running = jobs_service.enqueue_job(QUEUE_JOB_TYPE, "user")
        assert jobs_service.claim_pending_job(running.id) is True

        other = jobs_service.enqueue_job(QUEUE_JOB_TYPE, "other")
        # The active slot is taken: the claim loses without raising
        assert jobs_service.claim_pending_job(other.id) is False

        refreshed = jobs_service.get_job(other.id, QUEUE_JOB_TYPE)
        assert refreshed.status == "pending"
        assert refreshed.is_running is None

    def test_repeated_dispatch_is_idempotent(self, queue: JobsQueue, fake_backend: FakeBackend) -> None:
        result = queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert queue.dispatch_next(QUEUE_JOB_TYPE) is None
        assert queue.dispatch_next(QUEUE_JOB_TYPE) is None
        assert fake_backend.started_ids == [result.job_id]

    def test_dispatch_pending_scans_all_types(self, queue: JobsQueue, fake_backend: FakeBackend, jobs_service) -> None:
        first = queue.enqueue(QUEUE_JOB_TYPE, "user")
        second = queue.enqueue(QUEUE_JOB_TYPE, "user")

        jobs_service.update_job_status(first.job_id, "completed", job_type=QUEUE_JOB_TYPE)
        dispatched = queue.dispatch_pending()

        assert dispatched == [second.job_id]
        assert fake_backend.started_ids == [first.job_id, second.job_id]


class TestFailureHandling:
    def test_backend_failure_releases_slot_and_starts_next(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            JobIdentityResolver,
            "resolve",
            lambda self, username: {"username": username, "access_token": b"e", "access_secret": b"e"},
        )
        jobs_service = JobsService()
        backend = FakeBackend()
        queue = JobsQueue(backend=backend)

        first = queue.enqueue(QUEUE_JOB_TYPE, "user")
        second = queue.enqueue(QUEUE_JOB_TYPE, "user")

        # The running job fails; the slot must be released and the queue advance
        jobs_service.update_job_status(first.job_id, "failed", job_type=QUEUE_JOB_TYPE)
        assert queue.dispatch_next(QUEUE_JOB_TYPE) == second.job_id
        assert backend.started_ids == [first.job_id, second.job_id]

    def test_backend_submission_failure_marks_job_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            JobIdentityResolver,
            "resolve",
            lambda self, username: {"username": username, "access_token": b"e", "access_secret": b"e"},
        )
        jobs_service = JobsService()
        backend = FakeBackend()
        queue = JobsQueue(backend=backend)

        first = queue.enqueue(QUEUE_JOB_TYPE, "user")
        second = queue.enqueue(QUEUE_JOB_TYPE, "user")
        jobs_service.update_job_status(first.job_id, "completed", job_type=QUEUE_JOB_TYPE)

        # Now the backend explodes for the next job
        backend.fail_for = {second.job_id}
        third = queue.enqueue(QUEUE_JOB_TYPE, "user")

        failed = jobs_service.get_job(second.job_id, QUEUE_JOB_TYPE)
        assert failed.status == "failed"
        assert failed.is_running is None
        assert "Failed to start the job" in (failed.error_message or "")

        # The failure does not block the rest of the queue
        assert backend.started_ids == [first.job_id, third.job_id]

    def test_missing_credentials_fail_the_job_safely(self, fake_backend: FakeBackend, monkeypatch) -> None:
        def _no_creds(self, username: str) -> dict[str, Any]:
            raise JobCredentialsError("User credentials are no longer available; please log in again")

        monkeypatch.setattr(JobIdentityResolver, "resolve", _no_creds)
        jobs_service = JobsService()
        queue = JobsQueue(backend=fake_backend)

        result = queue.enqueue(QUEUE_JOB_TYPE, "user")

        job = jobs_service.get_job(result.job_id, QUEUE_JOB_TYPE)
        assert job.status == "failed"
        assert job.is_running is None
        assert "credentials" in (job.error_message or "").lower()
        assert fake_backend.started_ids == []

    def test_missing_payload_fails_the_job(self, fake_backend: FakeBackend, monkeypatch) -> None:
        monkeypatch.setattr(
            JobIdentityResolver,
            "resolve",
            lambda self, username: {"username": username, "access_token": b"e", "access_secret": b"e"},
        )
        jobs_service = JobsService()
        queue = JobsQueue(backend=fake_backend)

        running = queue.enqueue(QUEUE_JOB_TYPE, "user")
        queued = queue.enqueue(QUEUE_JOB_TYPE, "user")

        # The queued payload disappeared before dispatch
        assert queue.files_service.delete_payload(queued.job_id, QUEUE_JOB_TYPE) is True

        jobs_service.update_job_status(running.job_id, "completed", job_type=QUEUE_JOB_TYPE)
        queue.dispatch_next(QUEUE_JOB_TYPE)

        job = jobs_service.get_job(queued.job_id, QUEUE_JOB_TYPE)
        assert job.status == "failed"
        assert job.is_running is None
        assert "Missing payload" in (job.error_message or "")
        assert fake_backend.started_ids == [running.job_id]


class TestCancellation:
    def test_cancel_pending_never_invokes_backend(
        self, queue: JobsQueue, fake_backend: FakeBackend, jobs_service
    ) -> None:
        queue.enqueue(QUEUE_JOB_TYPE, "user")
        queued = queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert queue.cancel_pending(queued.job_id, QUEUE_JOB_TYPE) is True
        assert fake_backend.started_ids == [1]

        job = jobs_service.get_job(queued.job_id, QUEUE_JOB_TYPE)
        assert job.status == "cancelled"
        assert job.completed_at is not None

    def test_cancelled_pending_job_is_skipped_by_dispatcher(
        self, queue: JobsQueue, fake_backend: FakeBackend, jobs_service
    ) -> None:
        first = queue.enqueue(QUEUE_JOB_TYPE, "user")
        second = queue.enqueue(QUEUE_JOB_TYPE, "user")
        third = queue.enqueue(QUEUE_JOB_TYPE, "user")

        queue.cancel_pending(second.job_id, QUEUE_JOB_TYPE)
        jobs_service.update_job_status(first.job_id, "completed", job_type=QUEUE_JOB_TYPE)

        assert queue.dispatch_next(QUEUE_JOB_TYPE) == third.job_id
        assert fake_backend.started_ids == [first.job_id, third.job_id]

    def test_cancel_running_job_keeps_active_slot(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        result = queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert jobs_service.cancel_job_db(result.job_id, QUEUE_JOB_TYPE) is True

        job = jobs_service.get_job(result.job_id, QUEUE_JOB_TYPE)
        assert job.status == "cancelled"
        # The slot is still held until the execution really stopped
        assert job.is_running == 1
        assert jobs_service.has_running_job(QUEUE_JOB_TYPE) is True

        queued = queue.enqueue(QUEUE_JOB_TYPE, "user")
        assert queued.queued is True

    def test_slot_released_after_cancelled_execution_stops(
        self, queue: JobsQueue, fake_backend: FakeBackend, jobs_service: JobsService
    ) -> None:
        first = queue.enqueue(QUEUE_JOB_TYPE, "user")
        second = queue.enqueue(QUEUE_JOB_TYPE, "user")

        jobs_service.cancel_job_db(first.job_id, QUEUE_JOB_TYPE)
        # Nothing may start while the cancelled execution still holds the slot
        assert queue.dispatch_next(QUEUE_JOB_TYPE) is None

        # The worker reached its terminal state and released the slot
        jobs_service.update_job_status(first.job_id, "cancelled", job_type=QUEUE_JOB_TYPE)
        assert queue.dispatch_next(QUEUE_JOB_TYPE) == second.job_id
        assert fake_backend.started_ids == [first.job_id, second.job_id]

    def test_cancel_pending_of_running_job_returns_false(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        result = queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert queue.cancel_pending(result.job_id, QUEUE_JOB_TYPE) is False
        assert jobs_service.get_job(result.job_id, QUEUE_JOB_TYPE).status == "running"


class TestRecovery:
    def test_recover_dispatches_pending_jobs_after_restart(
        self, queue: JobsQueue, fake_backend: FakeBackend, jobs_service: JobsService
    ) -> None:
        queue.enqueue(QUEUE_JOB_TYPE, "user")
        queued = queue.enqueue(QUEUE_JOB_TYPE, "user")

        # Simulate a restart: the running job is gone and its slot was released
        jobs_service.update_job_status(1, "failed", job_type=QUEUE_JOB_TYPE)

        dispatched = queue.recover(force=True)

        assert dispatched == [queued.job_id]
        assert fake_backend.started_ids[-1] == queued.job_id

    def test_recover_releases_stale_slot_of_terminal_job(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        result = queue.enqueue(QUEUE_JOB_TYPE, "user")
        # Cancellation marked the job terminal but the worker disappeared
        jobs_service.cancel_job_db(result.job_id, QUEUE_JOB_TYPE)
        assert jobs_service.has_running_job(QUEUE_JOB_TYPE) is True

        released = jobs_service.release_stale_active_slots(grace_seconds=-1)

        assert released == 1
        assert jobs_service.has_running_job(QUEUE_JOB_TYPE) is False

    def test_recover_keeps_slot_of_recent_terminal_job(self, queue: JobsQueue, jobs_service: JobsService) -> None:
        result = queue.enqueue(QUEUE_JOB_TYPE, "user")
        jobs_service.cancel_job_db(result.job_id, QUEUE_JOB_TYPE)

        released = jobs_service.release_stale_active_slots(grace_seconds=300)

        assert released == 0
        assert jobs_service.has_running_job(QUEUE_JOB_TYPE) is True

    def test_repeated_recover_is_safe(self, queue: JobsQueue, fake_backend: FakeBackend) -> None:
        result = queue.enqueue(QUEUE_JOB_TYPE, "user")

        assert queue.recover(force=True) == []
        assert queue.recover(force=True) == []
        assert fake_backend.started_ids == [result.job_id]


class TestSanitizePayload:
    def test_removes_sensitive_keys(self) -> None:
        cleaned = sanitize_payload(
            {
                "csrf_token": "x",
                "access_token": b"secret",
                "access_secret": b"secret",
                "password": "p",
                "keep": "yes",
            }
        )

        assert cleaned == {"keep": "yes"}

    def test_handles_none(self) -> None:
        assert sanitize_payload(None) == {}
