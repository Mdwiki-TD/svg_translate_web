"""Unit tests for fix_nested_tasks service module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.main_app.public_jobs_workers.fix_nested_jobs.service import (
    start_fix_nested_tasks_job,
)


class TestStartFixNestedTasksJob:
    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service.threading.Thread")
    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service._register_cancel_event")
    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service.jobs_service")
    def test_start_job_creates_record(
        self,
        mock_jobs_service: MagicMock,
        mock_register: MagicMock,
        mock_thread: MagicMock,
    ) -> None:
        mock_job = MagicMock()
        mock_job.id = 42
        mock_jobs_service.create_job.return_value = mock_job

        job_id = start_fix_nested_tasks_job(
            title="Test.svg",
            args={"filename": "Test.svg"},
            user={"username": "testuser"},
        )

        mock_jobs_service.create_job.assert_called_once_with("fix_nested_tasks", "testuser")
        assert job_id == 42

    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service.threading.Thread")
    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service._register_cancel_event")
    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service.jobs_service")
    def test_start_job_with_no_user(
        self,
        mock_jobs_service: MagicMock,
        mock_register: MagicMock,
        mock_thread: MagicMock,
    ) -> None:
        mock_job = MagicMock()
        mock_job.id = 43
        mock_jobs_service.create_job.return_value = mock_job

        job_id = start_fix_nested_tasks_job(
            title="Test.svg",
            args={"filename": "Test.svg"},
            user=None,
        )

        mock_jobs_service.create_job.assert_called_once_with("fix_nested_tasks", None)
        assert job_id == 43

    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service.threading.Thread")
    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service._register_cancel_event")
    @patch("src.main_app.public_jobs_workers.fix_nested_tasks.service.jobs_service")
    def test_start_job_starts_thread(
        self,
        mock_jobs_service: MagicMock,
        mock_register: MagicMock,
        mock_thread: MagicMock,
    ) -> None:
        mock_job = MagicMock()
        mock_job.id = 44
        mock_jobs_service.create_job.return_value = mock_job

        start_fix_nested_tasks_job(
            title="Test.svg",
            args={"filename": "Test.svg"},
            user={"username": "testuser"},
        )

        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
