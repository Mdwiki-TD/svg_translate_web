"""Unit tests for jobs_worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.app.jobs_workers import jobs_worker
from src.app.jobs_workers.jobs_service import JobRecord


@pytest.fixture(autouse=True)
def clean_cancel_events():
    """Clear CANCEL_EVENTS before and after each test."""
    with jobs_worker.CANCEL_EVENTS_LOCK:
        jobs_worker.CANCEL_EVENTS.clear()
    yield
    with jobs_worker.CANCEL_EVENTS_LOCK:
        jobs_worker.CANCEL_EVENTS.clear()


@patch("src.app.jobs_workers.jobs_worker.jobs_service.create_job")
@patch("src.app.jobs_workers.jobs_worker.threading.Thread")
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
    assert isinstance(args[2], threading.Event)
    mock_thread_instance.start.assert_called_once()

    # Verify event was registered
    assert jobs_worker.get_cancel_event(1) is not None


@patch("src.app.jobs_workers.jobs_worker.jobs_service.create_job")
@patch("src.app.jobs_workers.jobs_worker.threading.Thread")
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

    # Verify event was registered
    assert jobs_worker.get_cancel_event(2) is not None


def test_cancel_job():
    """Test cancelling a registered job."""
    event = threading.Event()
    jobs_worker._register_cancel_event(123, event)

    assert not event.is_set()
    result = jobs_worker.cancel_job(123)
    assert result is True
    assert event.is_set()


def test_cancel_nonexistent_job():
    """Test cancelling a job that isn't registered."""
    result = jobs_worker.cancel_job(999)
    assert result is False


def test_runner_calls_target_and_cleans_up():
    """Test the internal _runner function."""
    mock_target = MagicMock()
    job_id = 456
    user = {"name": "test"}
    event = threading.Event()

    jobs_worker._register_cancel_event(job_id, event)
    assert jobs_worker.get_cancel_event(job_id) == event

    from src.app.jobs_workers.jobs_worker import _runner

    _runner(job_id, user, event, mock_target)

    mock_target.assert_called_once_with(job_id, user, cancel_event=event)
    # After runner finishes, event should be popped from CANCEL_EVENTS
    assert jobs_worker.get_cancel_event(job_id) is None
