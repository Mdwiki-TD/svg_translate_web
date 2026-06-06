"""Unit tests for base_worker module."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.base_worker import BaseJobWorker

# =============================================================================
# Tests for BaseJobWorker
# =============================================================================


class ConcreteTestWorker(BaseJobWorker):
    """Concrete implementation of BaseJobWorker for testing."""

    def __init__(self, job_id, user=None, cancel_event=None, should_fail=False, process_result=None):
        self.should_fail = should_fail
        self._process_result = process_result
        super().__init__(job_id, user, cancel_event)
        self.result = self.get_initial_result()

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
def mock_base_services(monkeypatch: pytest.MonkeyPatch, mock_jobs_service):
    """Mock the services used by BaseJobWorker."""
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    mock_generate_result_file_name = MagicMock(side_effect=lambda job_id, job_type: f"{job_type}_job_{job_id}.json")

    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.update_job_status",
        mock_update_job_status,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
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
        "is_job_cancelled": mock_jobs_service,
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
        worker = ConcreteTestWorker(job_id=1, user=None)
        result = worker.run()

        assert result["status"] == "completed"
        assert "item1" in result["items"]
        assert "completed_at" in result

        # Should update status to running, then completed
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
        worker = ConcreteTestWorker(job_id=1, user=None, cancel_event=cancel_event)

        assert worker.is_cancelled() is False

        cancel_event.set()
        assert worker.is_cancelled() is True
        assert worker.result["status"] == "cancelled"

    def test_before_run_returns_false_on_lookup_error(self, mock_base_services):
        """Test that before_run returns False when job not found."""
        mock_base_services["update_job_status"].side_effect = LookupError("Job not found")

        worker = ConcreteTestWorker(job_id=1, user=None)
        result = worker.before_run()

        assert result is False

    def test_handle_error(self, mock_base_services):
        """Test error handling method."""
        worker = ConcreteTestWorker(job_id=1, user=None)
        worker.handle_error(ValueError("Test error"), context="test context")

        assert worker.result["status"] == "failed"
        assert worker.result["error"] == "Test error"
        assert worker.result["error_type"] == "ValueError"

    def test_after_run_handles_save_exception(self, mock_base_services):
        """Test that after_run handles save exceptions gracefully."""
        mock_base_services["save_job_result_by_name"].side_effect = Exception("DB error")

        worker = ConcreteTestWorker(job_id=1, user=None)
        worker.after_run()  # Should not raise

        # Update should still be called
        mock_base_services["update_job_status"].assert_called()

    def test_after_run_handles_lookup_error(self, mock_base_services):
        """Test that after_run handles LookupError when updating status."""
        mock_base_services["update_job_status"].side_effect = LookupError("Job not found")

        worker = ConcreteTestWorker(job_id=1, user=None)
        worker.after_run()  # Should not raise

    def test_run_returns_early_when_before_run_fails(self, mock_base_services):
        """Test that run returns early when before_run returns False."""
        mock_base_services["update_job_status"].side_effect = LookupError("Job not found")

        worker = ConcreteTestWorker(job_id=1, user=None)
        result = worker.run()

        # Should return initial result without processing
        assert result["status"] == "pending"
