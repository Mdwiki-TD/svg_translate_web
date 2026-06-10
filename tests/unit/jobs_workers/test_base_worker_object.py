"""Unit tests for BaseObjectsJobWorker and WorkerObject."""

from __future__ import annotations

import threading
from unittest.mock import patch

import pytest

from src.main_app.jobs_workers.base_worker_object import (
    BaseObjectsJobWorker,
    WorkerObject,
)


class MockWorker(BaseObjectsJobWorker):
    def get_job_type(self) -> str:
        return "mock_job"

    def process(self) -> WorkerObject:
        return self.result


@pytest.fixture
def mock_db_services():
    with (
        patch("src.main_app.jobs_workers.base_worker_object.update_job_status") as m_update,
        patch("src.main_app.jobs_workers.base_worker_object.is_job_cancelled") as m_is_cancelled,
        patch("src.main_app.jobs_workers.base_worker_object.save_job_result_by_name") as m_save,
        patch("src.main_app.jobs_workers.base_worker_object.is_job_cancelled_file_exist") as m_file_exists,
    ):
        yield {
            "update": m_update,
            "is_cancelled": m_is_cancelled,
            "save": m_save,
            "file_exists": m_file_exists,
        }


@pytest.fixture
def worker():
    user = {"username": "testuser"}
    worker = MockWorker(job_id=123, user=user)
    worker.result = WorkerObject()
    return worker


def test_worker_object_to_json():
    obj = WorkerObject(status="running", error="some error")
    data = obj.to_json()
    assert data["status"] == "running"
    assert data["error"] == "some error"


class TestBaseObjectsJobWorker:
    def test_before_run_success(self, worker, mock_db_services):
        assert worker.before_run() is True
        mock_db_services["update"].assert_called_once_with(123, "running", worker.result_file, job_type="mock_job")
        assert worker.result.status == "running"

    def test_before_run_lookup_error(self, worker, mock_db_services):
        mock_db_services["update"].side_effect = LookupError("Not found")
        assert worker.before_run() is False

    def test_after_run_success(self, worker, mock_db_services):
        worker.result.status = "running"
        worker.after_run()
        assert worker.result.status == "completed"
        assert worker.result.completed_at is not None
        mock_db_services["update"].assert_called_with(123, "completed", worker.result_file, job_type="mock_job")

    def test_after_run_db_error(self, worker, mock_db_services):
        mock_db_services["update"].side_effect = Exception("DB Fail")
        worker.after_run()  # Should handle exception and log it

    def test_is_cancelled_event(self, worker):
        worker.cancel_event = threading.Event()
        worker.cancel_event.set()
        assert worker.is_cancelled() is True
        assert worker.result.status == "cancelled"

    def test_is_cancelled_file(self, worker, mock_db_services):
        mock_db_services["file_exists"].return_value = True
        assert worker.is_cancelled() is True
        assert worker.result.status == "cancelled"

    def test_is_cancelled_db(self, worker, mock_db_services):
        mock_db_services["is_cancelled"].return_value = True
        assert worker.is_cancelled(check_db=True) is True
        assert worker.result.status == "cancelled"

    def test_check_cancel_db_periodic(self, worker, mock_db_services):
        mock_db_services["is_cancelled"].return_value = True
        # Interval is 10
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

    def test_run_success(self, worker, mock_db_services):
        mock_db_services["update"].return_value = None
        result = worker.run()
        assert result["status"] == "completed"

    def test_run_before_fail(self, worker, mock_db_services):
        mock_db_services["update"].side_effect = LookupError()
        result = worker.run()
        assert result["status"] == "pending"  # remains pending if before_run fails

    def test_run_exception(self, worker, mock_db_services):
        with patch.object(MockWorker, "process", side_effect=Exception("Process failed")):
            result = worker.run()
            assert result["status"] == "failed"
            assert result["errors"][0]["error"] == "Process failed"
