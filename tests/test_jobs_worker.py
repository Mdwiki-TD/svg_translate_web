"""Unit tests for jobs_worker module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.app import jobs_worker
from src.app.jobs_service import JobRecord


@patch("src.app.jobs_worker.jobs_service.create_job")
@patch("src.app.jobs_worker.threading.Thread")
def test_start_collect_main_files_job(mock_thread, mock_create_job):
    """Test starting a collect main files job."""
    mock_job = JobRecord(id=1, job_type="collect_main_files", status="pending")
    mock_create_job.return_value = mock_job

    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    job_id = jobs_worker.start_collect_main_files_job()

    assert job_id == 1
    mock_create_job.assert_called_once_with("collect_main_files")
    mock_thread.assert_called_once()
    # Verify the thread was started with correct arguments
    args = mock_thread.call_args[1]["args"]
    assert args[0] == 1  # job_id
    assert args[1] is None  # user
    assert isinstance(args[2], jobs_worker.threading.Event)
    mock_thread_instance.start.assert_called_once()


@patch("src.app.jobs_worker.jobs_service.create_job")
@patch("src.app.jobs_worker.threading.Thread")
def test_start_fix_nested_main_files_job(mock_thread, mock_create_job):
    """Test starting a fix nested main files job."""
    mock_job = JobRecord(id=2, job_type="fix_nested_main_files", status="pending")
    mock_create_job.return_value = mock_job

    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    user = {"username": "test_user"}
    job_id = jobs_worker.start_fix_nested_main_files_job(user)

    assert job_id == 2
    mock_create_job.assert_called_once_with("fix_nested_main_files")
    mock_thread.assert_called_once()
    # Verify the thread was started with correct arguments
    args = mock_thread.call_args[1]["args"]
    assert args[0] == 2  # job_id
    assert args[1] == user
    assert isinstance(args[2], jobs_worker.threading.Event)
    mock_thread_instance.start.assert_called_once()
