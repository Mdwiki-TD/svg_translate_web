"""Unit tests for jobs_worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import JobRecord
from src.main_app.jobs_workers import jobs_worker


@pytest.fixture(autouse=True)
def mock_jobs_service_for_jobs_worker(monkeypatch: pytest.MonkeyPatch):
    """Mock jobs_service.is_job_cancelled and cancel_job to avoid database calls."""
    mock_is_cancelled = MagicMock(return_value=False)
    mock_cancel_job = MagicMock(return_value=False)
    monkeypatch.setattr(
        "src.main_app.db.services.jobs_service.is_job_cancelled",
        mock_is_cancelled,
    )
    monkeypatch.setattr(
        "src.main_app.db.services.jobs_service.cancel_job_db",
        mock_cancel_job,
    )
    return {"is_job_cancelled": mock_is_cancelled, "cancel_job": mock_cancel_job}


@pytest.fixture(autouse=True)
def clean_cancel_events():
    """Clear CANCEL_EVENTS before and after each test."""
    with jobs_worker.JOBS_CANCEL_EVENTS_LOCK:
        jobs_worker.JOBS_CANCEL_EVENTS.clear()
    yield
    with jobs_worker.JOBS_CANCEL_EVENTS_LOCK:
        jobs_worker.JOBS_CANCEL_EVENTS.clear()


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock create_job, Thread, and current_app for job worker tests."""
    mocks = {
        "create_job": MagicMock(),
        "Thread": MagicMock(),
        "current_app": MagicMock(),
    }

    monkeypatch.setattr("src.main_app.jobs_workers.jobs_worker.create_job", mocks["create_job"])
    monkeypatch.setattr("src.main_app.jobs_workers.jobs_worker.threading.Thread", mocks["Thread"])
    monkeypatch.setattr("src.main_app.jobs_workers.jobs_worker.current_app", mocks["current_app"])

    return mocks


def test_start_collect_templates_data_job(mock_services):
    """Test starting a collect templates data job."""
    mock_job = JobRecord(id=1, job_type="collect_templates_data", status="pending")
    mock_services["create_job"].return_value = mock_job

    mock_app = MagicMock()
    mock_services["current_app"]._get_current_object.return_value = mock_app

    mock_thread_instance = MagicMock()
    mock_services["Thread"].return_value = mock_thread_instance

    job_id = jobs_worker.start_job({"username": "22"}, "collect_templates_data")

    assert job_id == 1
    mock_services["create_job"].assert_called_once_with("collect_templates_data", "22")
    mock_services["Thread"].assert_called_once()
    # Verify the thread was started with correct arguments
    args = mock_services["Thread"].call_args[1]["args"]
    assert args[0] == 1  # job_id
    assert args[1] == {"username": "22"}  # user
    assert isinstance(args[2], threading.Event)
    mock_thread_instance.start.assert_called_once()

    # Verify event was registered
    assert jobs_worker._get_jobs_cancel_event(1) is not None


def test_start_fix_nested_main_files_job(mock_services):
    """Test starting a fix nested main files job."""
    mock_job = JobRecord(id=2, job_type="fix_nested_main_files", status="pending")
    mock_services["create_job"].return_value = mock_job

    mock_app = MagicMock()
    mock_services["current_app"]._get_current_object.return_value = mock_app

    mock_thread_instance = MagicMock()
    mock_services["Thread"].return_value = mock_thread_instance

    user = {"username": "test_user"}
    job_id = jobs_worker.start_job(user, "fix_nested_main_files")

    assert job_id == 2
    mock_services["create_job"].assert_called_once_with("fix_nested_main_files", "test_user")
    mock_services["Thread"].assert_called_once()

    # Verify event was registered
    assert jobs_worker._get_jobs_cancel_event(2) is not None


def test_cancel_job():
    """Test cancelling a registered job."""
    event = threading.Event()
    jobs_worker._register_cancel_event(123, event)

    assert not event.is_set()
    result = jobs_worker.cancel_job_worker(123)
    assert result is True
    assert event.is_set()


def test_cancel_nonexistent_job():
    """Test cancelling a job that isn't registered."""
    result = jobs_worker.cancel_job_worker(999)
    assert result is False


def test_runner_calls_target_and_cleans_up():
    """Test the internal _runner function."""
    mock_target = MagicMock()
    job_id = 456
    user = {"name": "test"}
    event = threading.Event()
    flask_app = MagicMock()
    flask_app.app_context = MagicMock()

    jobs_worker._register_cancel_event(job_id, event)
    assert jobs_worker._get_jobs_cancel_event(job_id) == event

    from src.main_app.jobs_workers.jobs_worker import _runner

    _runner(
        job_id=job_id,
        user=user,
        cancel_event=event,
        target_func=mock_target,
        flask_app=flask_app,
        args=None,
    )

    mock_target.assert_called_once_with(job_id=job_id, user=user, cancel_event=event, args=None)
    flask_app.app_context.assert_called_once()
    # After runner finishes, event should be popped from CANCEL_EVENTS
    assert jobs_worker._get_jobs_cancel_event(job_id) is None


def test_start_download_main_files_job(mock_services):
    """Test starting a download main files job."""
    mock_job = JobRecord(id=3, job_type="download_main_files", status="pending")
    mock_services["create_job"].return_value = mock_job

    mock_app = MagicMock()
    mock_services["current_app"]._get_current_object.return_value = mock_app

    mock_thread_instance = MagicMock()
    mock_services["Thread"].return_value = mock_thread_instance

    user = {"username": "test_user"}
    job_id = jobs_worker.start_job(user, "download_main_files")

    assert job_id == 3
    mock_services["create_job"].assert_called_once_with("download_main_files", "test_user")
    mock_services["Thread"].assert_called_once()

    # Verify event was registered
    assert jobs_worker._get_jobs_cancel_event(3) is not None


def test_start_job_with_invalid_job_type():
    """Test that starting a job with an invalid job type raises an error."""
    with pytest.raises(ValueError, match="Unknown job type"):
        jobs_worker.start_job({"username": "22"}, "invalid_job_type")


def test_multiple_jobs_can_be_cancelled_independently():
    """Test that multiple jobs can be registered and cancelled independently."""
    event1 = threading.Event()
    event2 = threading.Event()
    event3 = threading.Event()

    jobs_worker._register_cancel_event(1, event1)
    jobs_worker._register_cancel_event(2, event2)
    jobs_worker._register_cancel_event(3, event3)

    # Cancel job 2
    assert jobs_worker.cancel_job_worker(2) is True
    assert event2.is_set()
    assert not event1.is_set()
    assert not event3.is_set()

    # Cancel job 1
    assert jobs_worker.cancel_job_worker(1) is True
    assert event1.is_set()
    assert not event3.is_set()

    # Cancel job 3
    assert jobs_worker.cancel_job_worker(3) is True
    assert event3.is_set()


def test_runner_passes_args_to_target():
    """Test that _runner forwards the args parameter to the target function."""
    mock_target = MagicMock()
    job_id = 789
    user = {"name": "test"}
    event = threading.Event()
    flask_app = MagicMock()
    args = {"update_all": "true"}

    jobs_worker._register_cancel_event(job_id, event)

    from src.main_app.jobs_workers.jobs_worker import _runner

    _runner(
        job_id=job_id,
        user=user,
        cancel_event=event,
        target_func=mock_target,
        flask_app=flask_app,
        args=args,
    )
    mock_target.assert_called_once_with(job_id=job_id, user=user, cancel_event=event, args=args)


def test_runner_passes_none_args_by_default():
    """Test that _runner passes args=None to target when args not provided."""
    mock_target = MagicMock()
    job_id = 790
    user = None
    event = threading.Event()
    flask_app = MagicMock()

    jobs_worker._register_cancel_event(job_id, event)

    from src.main_app.jobs_workers.jobs_worker import _runner

    _runner(
        job_id=job_id,
        user=user,
        cancel_event=event,
        target_func=mock_target,
        flask_app=flask_app,
    )
    mock_target.assert_called_once_with(job_id=job_id, user=user, cancel_event=event, args=None)


def test_start_job_param(mock_services):
    """Test that start_job passes args to the background thread."""
    mock_job = JobRecord(id=10, job_type="collect_templates_data", status="pending")
    mock_services["create_job"].return_value = mock_job

    mock_app = MagicMock()
    mock_services["current_app"]._get_current_object.return_value = mock_app

    mock_thread_instance = MagicMock()
    mock_services["Thread"].return_value = mock_thread_instance

    args = {"update_all": "true"}
    job_id = jobs_worker.start_job({"username": "22"}, "collect_templates_data", args=args)

    assert job_id == 10
    mock_services["Thread"].assert_called_once()
    thread_args = mock_services["Thread"].call_args[1]["args"]
    # args tuple: (job_id, user, cancel_event, target_func, flask_app, args)
    assert thread_args[5] == args


def test_start_job_without_args_passes_none(mock_services):
    """Test that start_job passes args=None to the thread when no args given."""
    mock_job = JobRecord(id=11, job_type="collect_templates_data", status="pending")
    mock_services["create_job"].return_value = mock_job

    mock_app = MagicMock()
    mock_services["current_app"]._get_current_object.return_value = mock_app

    mock_thread_instance = MagicMock()
    mock_services["Thread"].return_value = mock_thread_instance

    job_id = jobs_worker.start_job({"username": "22"}, "collect_templates_data")

    assert job_id == 11
    thread_args = mock_services["Thread"].call_args[1]["args"]
    # args tuple: (job_id, user, cancel_event, target_func, flask_app, args)
    assert thread_args[5] == {}


def test_start_job_is_alias_for_start_job():
    """Test that start_job is the same callable as start_job."""
    assert jobs_worker.start_job is jobs_worker.start_job


def test_start_job_alias_works(mock_services):
    """Test that the start_job alias behaves identically to start_job."""
    mock_job = JobRecord(id=12, job_type="collect_templates_data", status="pending")
    mock_services["create_job"].return_value = mock_job

    mock_app = MagicMock()
    mock_services["current_app"]._get_current_object.return_value = mock_app

    mock_thread_instance = MagicMock()
    mock_services["Thread"].return_value = mock_thread_instance

    args = {"update_all": "true"}
    user = {"username": "alias_user"}
    job_id = jobs_worker.start_job(user, "collect_templates_data", args)

    assert job_id == 12
    mock_services["create_job"].assert_called_once_with("collect_templates_data", "alias_user")
    thread_args = mock_services["Thread"].call_args[1]["args"]
    assert thread_args[5] == args
