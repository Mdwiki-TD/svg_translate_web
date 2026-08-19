"""Unit tests for BaseObjectsJobWorker and WorkerMapping."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.database.services import JobsService
from src.main_app.jobs_workers.base_worker import (
    BaseObjectsJobWorker,
    WorkerMapping,
)
from src.main_app.jobs_workers.objects import JobsRunner


@pytest.fixture
def mock_base_worker(monkeypatch: pytest.MonkeyPatch):
    """Override parent conftest — keep file/mwclient mocks, let DB methods be real.

    Tests in this file assert on DB state changes, so ``update_job_status``
    and ``update_job_status_with_retry`` must not be mocked.
    """
    mocks = {
        "get_user_site": MagicMock(return_value=MagicMock(name="mw_site")),
        "save_job_result_by_name": MagicMock(),
    }
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker.get_user_site", mocks["get_user_site"])
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mocks["save_job_result_by_name"],
    )
    return mocks


class MockWorker(BaseObjectsJobWorker):
    def get_job_type(self) -> str:
        return "mock_job"

    def process(self) -> WorkerMapping:
        return self.result


@pytest.fixture
def mock_base_is_cancelled(
    monkeypatch: pytest.MonkeyPatch,
):
    mocks = {
        "is_job_cancelled_file_exist": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled_file_exist",
        mocks["is_job_cancelled_file_exist"],
    )
    return mocks


@pytest.fixture
def seeded_job():
    """Create a real JobRecord for the mock_job type."""
    svc = JobsService()
    job = svc.create_job(job_type="mock_job", username="testuser")
    return job


@pytest.fixture
def worker(seeded_job):
    user = {"username": "testuser"}
    worker = MockWorker(
        JobsRunner(
            job_id=seeded_job.id,
            user=user,
        )
    )
    worker.result = WorkerMapping()
    return worker


@pytest.fixture
def worker_no_job():
    """Worker without a real DB record — before_run will raise LookupError."""
    user = {"username": "testuser"}
    worker = MockWorker(
        JobsRunner(
            job_id=999,
            user=user,
        )
    )
    worker.result = WorkerMapping()
    return worker


def test_worker_object_to_json():
    obj = WorkerMapping(status="running", error="some error")
    data = obj.to_json()
    assert data["status"] == "running"
    assert data["error"] == "some error"


class TestBaseObjectsJobWorker:
    def test_before_run_success(self, worker, mock_base_worker, seeded_job):
        assert worker.before_run() is True
        assert worker.result.status == "running"
        job = JobsService().get_job(seeded_job.id, job_type="mock_job")
        assert job.status == "running"

    def test_before_run_lookup_error(self, worker_no_job, mock_base_worker):
        assert worker_no_job.before_run() is False

    def test_after_run_success(self, worker, mock_base_worker, seeded_job):
        worker.result.status = "running"
        worker.after_run()
        assert worker.result.status == "completed"
        assert worker.result.completed_at is not None
        job = JobsService().get_job(seeded_job.id, job_type="mock_job")
        assert job.status == "completed"

    def test_after_run_db_error(self, worker, mock_base_worker, seeded_job):
        worker.after_run()

    def test_is_cancelled_event(self, worker):
        worker.cancel_event = threading.Event()
        worker.cancel_event.set()
        assert worker.is_cancelled() is True
        assert worker.result.status == "cancelled"

    def test_is_cancelled_file(self, worker, mock_base_worker, mock_base_is_cancelled):
        mock_base_is_cancelled["is_job_cancelled_file_exist"].return_value = True
        assert worker.is_cancelled() is True
        assert worker.result.status == "cancelled"

    def test_is_cancelled_db(self, worker, mock_base_worker, seeded_job):
        svc = JobsService()
        svc.update_job_status(seeded_job.id, "cancelled", job_type="mock_job")
        assert worker.is_cancelled(check_db=True) is True
        assert worker.result.status == "cancelled"

    def test_check_cancel_db_periodic(self, worker, mock_base_worker, seeded_job):
        svc = JobsService()
        svc.update_job_status(seeded_job.id, "cancelled", job_type="mock_job")
        for _ in range(9):
            assert worker.check_cancel_db_periodic(interval=10) is False
        assert worker.check_cancel_db_periodic(interval=10) is True

    def test_get_priority(self, worker):
        assert worker.get_priority(5) == 1
        assert worker.get_priority(100) == 10

    def test_handle_error(self, worker):
        worker.handle_error(ValueError("Test error"), context="Some context")
        assert worker.result.status == "failed"
        assert worker.result.failed_at is not None
        assert worker.result.errors[0]["error"] == "Test error"
        assert worker.result.errors[0]["error_type"] == "ValueError"

    def test_log_no_site_error(self, worker):
        worker.log_no_site_error()
        assert worker.result.status == "failed"
        assert "No authenticated user site available" in worker.result.errors[0]["error"]

    def test_run_success(self, worker, mock_base_worker, seeded_job):
        result = worker.run()
        assert result["status"] == "completed"

    def test_run_before_fail(self, worker_no_job, mock_base_worker):
        result = worker_no_job.run()
        assert result["status"] == "pending"

    def test_run_exception(self, worker, mock_base_worker, seeded_job):
        with patch.object(MockWorker, "process", side_effect=Exception("Process failed")):
            result = worker.run()
            assert result["status"] == "failed"
            assert result["errors"][0]["error"] == "Process failed"
