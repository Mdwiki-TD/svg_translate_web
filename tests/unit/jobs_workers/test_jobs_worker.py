"""Unit tests for src/main_app/jobs_workers/jobs_worker.py.

Uses real DB (TestingConfig SQLite) for JobsService calls.
Mocks only external/non-DB dependencies:
- threading.Thread (prevents background execution)
- jobs_data_admins (test job registry)
- create_cancel_file (filesystem)
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from src.main_app.database.services import JobsService, UsersService
from src.main_app.jobs.backends.thread_cancel_registry import (
    get_cancel_event,
    pop_cancel_event,
    register_cancel_event,
)
from src.main_app.jobs.jobs_lifetime.jobs_canceller import JobCanceller
from src.main_app.jobs.jobs_lifetime.jobs_starter import JobStarter


def test_cancel_event_management():
    job_id = 999
    event = threading.Event()

    register_cancel_event(job_id, event)
    assert get_cancel_event(job_id) is event

    popped = pop_cancel_event(job_id)
    assert popped is event
    assert get_cancel_event(job_id) is None


@pytest.fixture
def mock_load_job_data(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    _mock.return_value = MagicMock()
    monkeypatch.setattr("src.main_app.jobs.job_executor.load_job_data", _mock)
    monkeypatch.setattr("src.main_app.jobs.jobs_lifetime.job_creator.load_job_data", _mock)
    return _mock


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.job_service = JobsService()


@pytest.mark.usefixtures("mock_app")
class TestCancelJobWorker(TestSetup):
    def test_cancel_job_worker(self, mock_app: Flask):
        """JobCanceller.cancel should set the event, update the DB, and create a cancelled file."""
        with mock_app.app_context():
            job = self.job_service.create_job("test_job", "testuser")
            job_id = job.id
            # Set result_file so the cancelled-file branch executes
            self.job_service.update_job_status(job_id, "running", "test_job_job_1.json", job_type="test_job")
            # Re-fetch to get the updated result_file
            job = self.job_service.get_job(job_id, "test_job")

        event = threading.Event()
        register_cancel_event(job_id, event)

        mock_jobs_files_service = MagicMock()
        mock_jobs_files_service.create_cancel_file = MagicMock(
            return_value=MagicMock()
        )  # Simulate file creation success

        with mock_app.app_context():
            result = JobCanceller(mock_jobs_files_service).cancel(job_id, "test_job", job)

        assert result is True
        assert event.is_set()

        # Verify DB was updated
        with mock_app.app_context():
            assert self.job_service.is_job_cancelled(job_id) is True

        mock_jobs_files_service.create_cancel_file.assert_called_once()

        # Clean up
        pop_cancel_event(job_id)


@pytest.mark.usefixtures("mock_app")
class TestStartJob(TestSetup):
    @patch("src.main_app.jobs.backends.thread_backend.threading.Thread")
    def test_start_job(self, mock_thread, mock_app: Flask, mock_load_job_data):
        """JobStarter.start should create a DB record, register cancel event, and spawn a thread."""
        with mock_app.app_context():
            UsersService().create_user("test_user")

        user_payload = {"username": "test_user"}
        job_type = "test_type"

        mock_job_data = MagicMock()
        mock_job_data.job_class = MagicMock()
        mock_job_data.job_args = []  # Empty args to avoid SettingsService
        mock_load_job_data.return_value = mock_job_data

        with mock_app.app_context():
            job_id = JobStarter().start(user_payload, job_type, {"arg": 1})

        assert job_id is not None
        assert job_id > 0
        mock_thread.assert_called_once()
        assert get_cancel_event(job_id) is not None

        # Verify job was persisted to the real DB
        with mock_app.app_context():
            job = self.job_service.get_job(job_id, job_type)
            assert job is not None
            assert job.status == "pending"
            assert job.username == "test_user"

        # Clean up
        pop_cancel_event(job_id)
