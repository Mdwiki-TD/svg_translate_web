"""Unit tests for jobs_worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.app import jobs_worker
from src.app.jobs_service import JobRecord


@pytest.fixture(autouse=True)
def clean_cancel_events():
    """Clear CANCEL_EVENTS before and after each test."""
    with jobs_worker.CANCEL_EVENTS_LOCK:
        jobs_worker.CANCEL_EVENTS.clear()
    yield
    with jobs_worker.CANCEL_EVENTS_LOCK:
        jobs_worker.CANCEL_EVENTS.clear()


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
    assert isinstance(args[2], threading.Event)
    mock_thread_instance.start.assert_called_once()

    # Verify event was registered
    assert jobs_worker.get_cancel_event(1) is not None


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

    # We need to mock the jobs_targets dictionary indirectly
    # since it's defined inside start_job.
    # Alternatively, we can just test _runner directly if we can access it.
    # It is not exported, but it's in the module.

    with patch.dict("src.app.jobs_worker.CANCEL_EVENTS", {job_id: event}):
        # Mock the worker function that would be called
        def fake_worker(jid, usr, cancel_event):
            mock_target(jid, usr, cancel_event)

        # Instead of patching jobs_targets (which is local),
        # let's just test that the finally block in _runner works.
        # We can simulate _runner's logic.

        # Test start_job which sets up the runner
        with patch("src.app.jobs_worker.jobs_service.create_job") as mock_create:
            mock_create.return_value = JobRecord(id=job_id, job_type="collect_main_files", status="pending")
            with patch("src.app.jobs_worker.collect_main_files_for_templates", mock_target):
                # We want to check if _runner pops the event.
                # Since _runner is inside start_job, we have to start it.

                # To test _runner specifically, we can extract it if we had a way,
                # but let's just look at how it's used.
                pass

    # Let's try to test _runner by calling it if possible
    from src.app.jobs_worker import _runner

    _runner(job_id, user, event)

    assert mock_target.called
    # After runner finishes, event should be popped
    assert jobs_worker.get_cancel_event(job_id) is None
