"""Unit tests for src/main_app/jobs_workers/jobs_worker.py.

Uses real DB (TestingConfig SQLite) for JobsService calls.
Mocks only external/non-DB dependencies:
- threading.Thread (prevents background execution)
- jobs_data_public (test job registry)
- create_cancel_file (filesystem)
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from src.main_app.database.services import JobsService, UsersService
from src.main_app.jobs_workers.backends.thread_backend import _runner
from src.main_app.jobs_workers.jobs_lifetime.cancel_registry import (
    get_cancel_event,
    pop_cancel_event,
    register_cancel_event,
)
from src.main_app.jobs_workers.jobs_lifetime.jobs_canceller import JobCanceller
from src.main_app.jobs_workers.jobs_lifetime.jobs_starter import JobStarter
from src.main_app.jobs_workers.objects import JobsRunner


def test_cancel_event_management():
    job_id = 999
    event = threading.Event()

    register_cancel_event(job_id, event)
    assert get_cancel_event(job_id) is event

    popped = pop_cancel_event(job_id)
    assert popped is event
    assert get_cancel_event(job_id) is None


def test_runner():
    job_id = 1
    user = {"username": "test"}
    cancel_event = threading.Event()

    target_class = MagicMock()
    target_class.run = MagicMock()

    _mock = MagicMock()
    _mock.return_value = target_class

    src = Flask(__name__)
    args = {"foo": "bar"}
    data = JobsRunner(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
        form_data=None,
    )

    register_cancel_event(job_id, cancel_event)

    _runner(data, _mock, src)

    target_class.run.assert_called_once_with()
    assert get_cancel_event(job_id) is None


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.job_service = JobsService()


@pytest.mark.usefixtures("mock_app")
class TestCancelJobWorker(TestSetup):
    @patch("src.main_app.jobs_workers.jobs_lifetime.jobs_canceller.JobFilesService.create_cancel_file")
    def test_cancel_job_worker(self, mock_create_file, mock_app: Flask):
        """cancel_job_worker should set the event, update the DB, and create a cancelled file."""
        with mock_app.app_context():
            job = self.job_service.create_job("test_job", "testuser")
            job_id = job.id
            # Set result_file so the cancelled-file branch executes
            self.job_service.update_job_status(job_id, "running", "test_job_job_1.json", job_type="test_job")
            # Re-fetch to get the updated result_file
            job = self.job_service.get_job(job_id, "test_job")

        event = threading.Event()
        register_cancel_event(job_id, event)
        mock_create_file.return_value = MagicMock()  # Simulate file creation success

        with mock_app.app_context():
            result = JobCanceller().cancel(job_id, "test_job", job)

        assert result is True
        assert event.is_set()

        # Verify DB was updated
        with mock_app.app_context():
            assert self.job_service.is_job_cancelled(job_id) is True

        mock_create_file.assert_called_once()

        # Clean up
        pop_cancel_event(job_id)


@pytest.mark.usefixtures("mock_app")
class TestStartJob(TestSetup):
    @patch("src.main_app.jobs_workers.backends.thread_backend.threading.Thread")
    @patch("src.main_app.jobs_workers.jobs_lifetime.jobs_starter.jobs_data_public")
    def test_start_job(self, mock_jobs_data, mock_thread, mock_app: Flask):
        """JobStarter().start should create a DB record, register cancel event, and spawn a thread."""
        with mock_app.app_context():
            UsersService().create_user("test_user")

        user_payload = {"username": "test_user"}
        job_type = "test_type"

        mock_job_data = MagicMock()
        mock_job_data.job_class = MagicMock()
        mock_job_data.job_args = []  # Empty args to avoid SettingsService
        mock_jobs_data.get.return_value = mock_job_data

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
