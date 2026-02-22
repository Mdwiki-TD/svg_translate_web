"""Unit tests for jobs_worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers import jobs_worker
from src.main_app.jobs_workers.jobs_service import JobRecord


@pytest.fixture(autouse=True)
def clean_cancel_events():
    """Clear CANCEL_EVENTS before and after each test."""
    with jobs_worker.CANCEL_EVENTS_LOCK:
        jobs_worker.CANCEL_EVENTS.clear()
    yield
    with jobs_worker.CANCEL_EVENTS_LOCK:
        jobs_worker.CANCEL_EVENTS.clear()


@patch("src.main_app.jobs_workers.jobs_worker.jobs_service.create_job")
@patch("src.main_app.jobs_workers.jobs_worker.threading.Thread")
def test_start_collect_main_files_job(mock_thread, mock_create_job):
    """Test starting a collect main files job."""
    mock_job = JobRecord(id=1, job_type="collect_main_files", status="pending")
    mock_create_job.return_value = mock_job

    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    job_id = jobs_worker.start_job(None, "collect_main_files")

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


@patch("src.main_app.jobs_workers.jobs_worker.jobs_service.create_job")
@patch("src.main_app.jobs_workers.jobs_worker.threading.Thread")
def test_start_fix_nested_main_files_job(mock_thread, mock_create_job):
    """Test starting a fix nested main files job."""
    mock_job = JobRecord(id=2, job_type="fix_nested_main_files", status="pending")
    mock_create_job.return_value = mock_job

    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    user = {"username": "test_user"}
    job_id = jobs_worker.start_job(user, "fix_nested_main_files")

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

    from src.main_app.jobs_workers.jobs_worker import _runner

    _runner(job_id, user, event, mock_target)

    mock_target.assert_called_once_with(job_id, user, cancel_event=event)
    # After runner finishes, event should be popped from CANCEL_EVENTS
    assert jobs_worker.get_cancel_event(job_id) is None


@patch("src.main_app.jobs_workers.jobs_worker.jobs_service.create_job")
@patch("src.main_app.jobs_workers.jobs_worker.threading.Thread")
def test_start_download_main_files_job(mock_thread, mock_create_job):
    """Test starting a download main files job."""
    mock_job = JobRecord(id=3, job_type="download_main_files", status="pending")
    mock_create_job.return_value = mock_job

    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    user = {"username": "test_user"}
    job_id = jobs_worker.start_job(user, "download_main_files")

    assert job_id == 3
    mock_create_job.assert_called_once_with("download_main_files")
    mock_thread.assert_called_once()

    # Verify event was registered
    assert jobs_worker.get_cancel_event(3) is not None


def test_start_job_with_invalid_job_type():
    """Test that starting a job with an invalid job type raises an error."""
    with pytest.raises(ValueError, match="Unknown job type"):
        jobs_worker.start_job(None, "invalid_job_type")


def test_multiple_jobs_can_be_cancelled_independently():
    """Test that multiple jobs can be registered and cancelled independently."""
    event1 = threading.Event()
    event2 = threading.Event()
    event3 = threading.Event()

    jobs_worker._register_cancel_event(1, event1)
    jobs_worker._register_cancel_event(2, event2)
    jobs_worker._register_cancel_event(3, event3)

    # Cancel job 2
    assert jobs_worker.cancel_job(2) is True
    assert event2.is_set()
    assert not event1.is_set()
    assert not event3.is_set()

    # Cancel job 1
    assert jobs_worker.cancel_job(1) is True
    assert event1.is_set()
    assert not event3.is_set()

    # Cancel job 3
    assert jobs_worker.cancel_job(3) is True
    assert event3.is_set()