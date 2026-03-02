"""Unit tests for base_worker module."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.base_worker import BaseJobWorker, job_exception_handler


class TestJobExceptionHandler:
    """Tests for the job_exception_handler decorator."""

    def test_successful_function_returns_result(self):
        """Test that decorated function returns result on success."""

        @job_exception_handler("result.json", 1, "test_job")
        def successful_func():
            return {"status": "completed"}

        result = successful_func()
        assert result == {"status": "completed"}

    def test_exception_is_caught_and_logged(self):
        """Test that exceptions are caught and logged."""

        @job_exception_handler("result.json", 1, "test_job")
        def failing_func():
            raise ValueError("Test error")

        with patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.save_job_result_by_name"
        ) as mock_save, patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.update_job_status"
        ) as mock_update:
            result = failing_func()

        assert result is None
        mock_save.assert_called_once()
        mock_update.assert_called_once_with(1, "failed", "result.json", job_type="test_job")

    def test_exception_saves_error_details(self):
        """Test that error details are saved when exception occurs."""

        @job_exception_handler("result.json", 1, "test_job")
        def failing_func():
            raise RuntimeError("Unexpected failure")

        with patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.save_job_result_by_name"
        ) as mock_save, patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.update_job_status"
        ):
            failing_func()

        saved_result = mock_save.call_args[0][1]
        assert saved_result["job_id"] == 1
        assert saved_result["error"] == "Unexpected failure"
        assert saved_result["error_type"] == "RuntimeError"
        assert "completed_at" in saved_result

    def test_handles_lookup_error_when_saving(self):
        """Test that LookupError when saving/updating is handled gracefully."""

        @job_exception_handler("result.json", 1, "test_job")
        def failing_func():
            raise ValueError("Test error")

        with patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.save_job_result_by_name"
        ) as mock_save:
            mock_save.side_effect = LookupError("Job not found")
            result = failing_func()

        assert result is None

    def test_handles_exception_when_saving_error_result(self):
        """Test that exceptions when saving error result are handled."""

        @job_exception_handler("result.json", 1, "test_job")
        def failing_func():
            raise ValueError("Test error")

        with patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.save_job_result_by_name"
        ) as mock_save, patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.update_job_status"
        ) as mock_update:
            mock_save.side_effect = Exception("Database connection failed")
            mock_update.return_value = None
            result = failing_func()

        assert result is None
        mock_update.assert_called()

    def test_handles_lookup_error_in_fallback_update(self):
        """Test that LookupError in fallback update is handled."""

        @job_exception_handler("result.json", 1, "test_job")
        def failing_func():
            raise ValueError("Test error")

        with patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.save_job_result_by_name"
        ) as mock_save, patch(
            "src.main_app.jobs_workers.base_worker.jobs_service.update_job_status"
        ) as mock_update:
            mock_save.side_effect = Exception("DB error")
            mock_update.side_effect = LookupError("Job not found")
            result = failing_func()

        assert result is None


class ConcreteTestWorker(BaseJobWorker):
    """Concrete implementation of BaseJobWorker for testing."""

    def __init__(self, job_id, user=None, cancel_event=None, should_fail=False, process_result=None):
        self.should_fail = should_fail
        self._process_result = process_result
        super().__init__(job_id, user, cancel_event)

    def get_job_type(self) -> str:
        return "test_worker"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "status": "pending",
            "items": [],
        }

    def process(self) -> Dict[str, Any]:
        if self.should_fail:
            raise RuntimeError("Processing failed")
        if self._process_result:
            return self._process_result
        self.result["items"].append("item1")
        self.result["status"] = "completed"
        return self.result


@pytest.fixture
def mock_base_services(monkeypatch):
    """Mock the services used by BaseJobWorker."""
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    mock_generate_result_file_name = MagicMock(side_effect=lambda job_id, job_type: f"{job_type}_job_{job_id}.json")

    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.jobs_service.update_job_status",
        mock_update_job_status,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.jobs_service.save_job_result_by_name",
        mock_save_job_result,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.generate_result_file_name",
        mock_generate_result_file_name,
    )

    return {
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "generate_result_file_name": mock_generate_result_file_name,
    }


class TestBaseJobWorker:
    """Tests for the BaseJobWorker class."""

    def test_worker_initialization(self, mock_base_services):
        """Test that worker is initialized correctly."""
        worker = ConcreteTestWorker(job_id=1, user={"username": "test"})
        assert worker.job_id == 1
        assert worker.user == {"username": "test"}
        assert worker.job_type == "test_worker"
        assert worker.result_file == "test_worker_job_1.json"
        assert worker.result["job_id"] == 1

    def test_successful_run(self, mock_base_services):
        """Test successful job run."""
        worker = ConcreteTestWorker(job_id=1)
        result = worker.run()
        assert result["status"] == "completed"
        assert "item1" in result["items"]
        assert "completed_at" in result
        assert mock_base_services["update_job_status"].call_count == 2
        mock_base_services["save_job_result_by_name"].assert_called()

    def test_failed_run(self, mock_base_services):
        """Test job run that fails with exception."""
        worker = ConcreteTestWorker(job_id=1, should_fail=True)
        result = worker.run()
        assert result["status"] == "failed"
        assert "error" in result
        assert result["error_type"] == "RuntimeError"

    def test_is_cancelled(self, mock_base_services):
        """Test cancellation detection."""
        cancel_event = threading.Event()
        worker = ConcreteTestWorker(job_id=1, cancel_event=cancel_event)
        assert worker.is_cancelled() is False
        cancel_event.set()
        assert worker.is_cancelled() is True
        assert worker.result["status"] == "cancelled"

    def test_before_run_returns_false_on_lookup_error(self, mock_base_services):
        """Test that before_run returns False when job not found."""
        mock_base_services["update_job_status"].side_effect = LookupError("Job not found")
        worker = ConcreteTestWorker(job_id=1)
        result = worker.before_run()
        assert result is False

    def test_handle_error(self, mock_base_services):
        """Test error handling method."""
        worker = ConcreteTestWorker(job_id=1)
        worker.handle_error(ValueError("Test error"), context="test context")
        assert worker.result["status"] == "failed"
        assert worker.result["error"] == "Test error"
        assert worker.result["error_type"] == "ValueError"

    def test_after_run_handles_save_exception(self, mock_base_services):
        """Test that after_run handles save exceptions gracefully."""
        mock_base_services["save_job_result_by_name"].side_effect = Exception("DB error")
        worker = ConcreteTestWorker(job_id=1)
        worker.after_run()
        mock_base_services["update_job_status"].assert_called()

    def test_after_run_handles_lookup_error(self, mock_base_services):
        """Test that after_run handles LookupError when updating status."""
        mock_base_services["update_job_status"].side_effect = LookupError("Job not found")
        worker = ConcreteTestWorker(job_id=1)
        worker.after_run()

    def test_run_returns_early_when_before_run_fails(self, mock_base_services):
        """Test that run returns early when before_run returns False."""
        mock_base_services["update_job_status"].side_effect = LookupError("Job not found")
        worker = ConcreteTestWorker(job_id=1)
        result = worker.run()
        assert result["status"] == "pending"
