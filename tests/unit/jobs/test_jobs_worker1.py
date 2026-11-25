"""Unit tests for jobs_worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest
from src.main_app.database.models import JobRecord
from src.main_app.jobs.backends import thread_cancel_registry
from src.main_app.jobs.backends.thread_cancel_registry import (
    get_cancel_event,
    register_cancel_event,
)
from src.main_app.jobs.jobs_lifetime.jobs_canceller import JobCanceller
from src.main_app.jobs.jobs_lifetime.jobs_starter import JobStarter
from src.main_app.jobs_workers.objects import JobData


@pytest.fixture(autouse=True)
def mock_jobs_service_for_jobs_worker(monkeypatch: pytest.MonkeyPatch):
    """Mock jobs_service.is_job_cancelled and cancel_job to avoid database calls."""
    mock_is_cancelled = MagicMock(return_value=False)
    mock_cancel_job = MagicMock(return_value=False)
    monkeypatch.setattr(
        "src.main_app.database.services.jobs_service.JobsService.is_job_cancelled",
        mock_is_cancelled,
    )
    monkeypatch.setattr(
        "src.main_app.database.services.jobs_service.JobsService.cancel_job_db",
        mock_cancel_job,
    )
    return {"is_job_cancelled": mock_is_cancelled, "cancel_job": mock_cancel_job}


@pytest.fixture(autouse=True)
def clean_cancel_events():
    """Clear CANCEL_EVENTS before and after each test."""
    with thread_cancel_registry.JOBS_CANCEL_EVENTS_LOCK:
        thread_cancel_registry.JOBS_CANCEL_EVENTS.clear()
    yield
    with thread_cancel_registry.JOBS_CANCEL_EVENTS_LOCK:
        thread_cancel_registry.JOBS_CANCEL_EVENTS.clear()


@pytest.fixture
def mock_jobs_worker_services(monkeypatch: pytest.MonkeyPatch):
    """Mock JobCreator, BackendRegistry, and load_job_data for job starter tests."""
    mock_create = MagicMock()
    mock_get_backend_name = MagicMock(return_value="thread")
    mock_get_backend = MagicMock()
    mock_load_job_data = MagicMock()

    monkeypatch.setattr("src.main_app.jobs.jobs_lifetime.job_creator.JobCreator.create", mock_create)
    monkeypatch.setattr(
        "src.main_app.jobs.jobs_lifetime.jobs_starter.BackendRegistry.get_backend_name", mock_get_backend_name
    )
    monkeypatch.setattr("src.main_app.jobs.jobs_lifetime.jobs_starter.BackendRegistry.get_backend", mock_get_backend)
    monkeypatch.setattr("src.main_app.jobs.jobs_lifetime.job_creator.load_job_data", mock_load_job_data)

    return {
        "create": mock_create,
        "get_backend_name": mock_get_backend_name,
        "get_backend": mock_get_backend,
        "load_job_data": mock_load_job_data,
    }


def test_start_collect_templates_data_job(mock_jobs_worker_services):
    """Test starting a collect templates data job."""
    mock_job = JobRecord(id=1, job_type="collect_templates_data", status="pending")
    mock_job_data = JobData(job_type="collect_templates_data", job_name="Test", job_class=MagicMock())
    mock_backend = MagicMock()

    from src.main_app.jobs.jobs_lifetime.job_creator import CreatedJob

    mock_jobs_worker_services["create"].return_value = CreatedJob(job=mock_job, job_data=mock_job_data, payload={})
    mock_jobs_worker_services["get_backend"].return_value = mock_backend

    job_id = JobStarter().start({"username": "22"}, "collect_templates_data")

    assert job_id == 1
    mock_jobs_worker_services["create"].assert_called_once()
    mock_backend.start.assert_called_once_with(mock_job, mock_job_data, user={"username": "22"})


def test_start_fix_nested_main_files_job(mock_jobs_worker_services):
    """Test starting a fix nested main files job."""
    mock_job = JobRecord(id=2, job_type="fix_nested_main_files", status="pending")
    mock_job_data = JobData(job_type="fix_nested_main_files", job_name="Test", job_class=MagicMock())
    mock_backend = MagicMock()

    from src.main_app.jobs.jobs_lifetime.job_creator import CreatedJob

    mock_jobs_worker_services["create"].return_value = CreatedJob(job=mock_job, job_data=mock_job_data, payload={})
    mock_jobs_worker_services["get_backend"].return_value = mock_backend

    user = {"username": "test_user"}
    job_id = JobStarter().start(user, "fix_nested_main_files")

    assert job_id == 2
    mock_jobs_worker_services["create"].assert_called_once()
    mock_backend.start.assert_called_once_with(mock_job, mock_job_data, user=user)


def test_cancel_job():
    """Test cancelling a registered job."""
    event = threading.Event()
    register_cancel_event(123, event)

    mock_job = JobRecord(id=123, job_type="test_type", status="running", backend="thread")

    mock_jobs_service = MagicMock()
    mock_jobs_service.cancel_job_db.return_value = True
    mock_jobs_service.get_by.return_value = mock_job

    mock_jobs_files_service = MagicMock()
    mock_jobs_files_service.create_cancel_file.return_value = MagicMock()

    # Use the real ThreadBackend so cancel() sets the in-process event
    from src.main_app.jobs.backends.thread_backend import ThreadBackend

    mock_backend_registry = MagicMock()
    mock_backend_registry.get_backend.return_value = ThreadBackend()

    assert not event.is_set()
    result = JobCanceller(
        jobs_files_service=mock_jobs_files_service,
        jobs_service=mock_jobs_service,
        backend_registry=mock_backend_registry,
    ).cancel(123)
    assert result is True
    assert event.is_set()


def test_cancel_nonexistent_job():
    """Test cancelling a job that isn't registered."""
    mock_jobs_service = MagicMock()
    mock_jobs_service.get_by.return_value = None
    mock_jobs_service.cancel_job_db.return_value = False

    mock_jobs_files_service = MagicMock()

    result = JobCanceller(
        jobs_files_service=mock_jobs_files_service,
        jobs_service=mock_jobs_service,
    ).cancel(999)
    assert result is False


def test_runner_calls_target_and_cleans_up(monkeypatch: pytest.MonkeyPatch):
    """Test the internal _runner function."""
    job_id = 456
    user = {"name": "test"}
    event = threading.Event()
    flask_app = MagicMock()
    flask_app.app_context = MagicMock()

    register_cancel_event(job_id, event)
    assert get_cancel_event(job_id) == event

    mock_executor_instance = MagicMock()
    mock_executor_instance.run.return_value = 0

    monkeypatch.setattr(
        "src.main_app.jobs.job_executor.JobExecutor",
        lambda *a, **kw: mock_executor_instance,
    )

    from src.main_app.jobs.backends.thread_backend import _runner

    _runner(
        job_id=job_id,
        user=user,
        cancel_event=event,
        flask_app=flask_app,
    )
    mock_executor_instance.run.assert_called_once_with(job_id, user=user, cancel_event=event)
    flask_app.app_context.assert_called_once()
    # After runner finishes, event should be popped from CANCEL_EVENTS
    assert get_cancel_event(job_id) is None


def test_start_download_main_files_job(mock_jobs_worker_services):
    """Test starting a download main files job."""
    mock_job = JobRecord(id=3, job_type="download_main_files", status="pending")
    mock_job_data = JobData(job_type="download_main_files", job_name="Test", job_class=MagicMock())
    mock_backend = MagicMock()

    from src.main_app.jobs.jobs_lifetime.job_creator import CreatedJob

    mock_jobs_worker_services["create"].return_value = CreatedJob(job=mock_job, job_data=mock_job_data, payload={})
    mock_jobs_worker_services["get_backend"].return_value = mock_backend

    user = {"username": "test_user"}
    job_id = JobStarter().start(user, "download_main_files")

    assert job_id == 3
    mock_jobs_worker_services["create"].assert_called_once()
    mock_backend.start.assert_called_once()


def test_start_job_with_invalid_job_type():
    """Test that starting a job with an invalid job type raises an error."""
    with pytest.raises(ValueError, match="Unknown job type"):
        JobStarter().start({"username": "22"}, "invalid_job_type")


def test_multiple_jobs_can_be_cancelled_independently():
    """Test that multiple jobs can be registered and cancelled independently."""
    event1 = threading.Event()
    event2 = threading.Event()
    event3 = threading.Event()

    register_cancel_event(1, event1)
    register_cancel_event(2, event2)
    register_cancel_event(3, event3)

    mock_jobs_service = MagicMock()
    mock_jobs_service.cancel_job_db.return_value = True

    mock_jobs_files_service = MagicMock()
    mock_jobs_files_service.create_cancel_file.return_value = MagicMock()

    # Use the real ThreadBackend so cancel() sets the in-process events
    from src.main_app.jobs.backends.thread_backend import ThreadBackend

    mock_backend_registry = MagicMock()
    mock_backend_registry.get_backend.return_value = ThreadBackend()

    job_canceller = JobCanceller(
        jobs_files_service=mock_jobs_files_service,
        jobs_service=mock_jobs_service,
        backend_registry=mock_backend_registry,
    )

    # Cancel job 2
    job2 = JobRecord(id=2, job_type="test_type_2", status="running", backend="thread")
    mock_jobs_service.get_by.return_value = job2
    assert job_canceller.cancel(2) is True
    assert event2.is_set()
    assert not event1.is_set()
    assert not event3.is_set()

    # Cancel job 1
    job1 = JobRecord(id=1, job_type="test_type_1", status="running", backend="thread")
    mock_jobs_service.get_by.return_value = job1
    assert job_canceller.cancel(1) is True
    assert event1.is_set()
    assert not event3.is_set()

    # Cancel job 3
    job3 = JobRecord(id=3, job_type="test_type_3", status="running", backend="thread")
    mock_jobs_service.get_by.return_value = job3
    assert job_canceller.cancel(3) is True
    assert event3.is_set()


def test_runner_passes_args_to_target(monkeypatch: pytest.MonkeyPatch):
    """Test that _runner forwards args through JobExecutor."""
    job_id = 789
    user = {"name": "test"}
    event = threading.Event()
    flask_app = MagicMock()

    register_cancel_event(job_id, event)

    mock_executor_instance = MagicMock()
    mock_executor_instance.run.return_value = 0

    monkeypatch.setattr(
        "src.main_app.jobs.job_executor.JobExecutor",
        lambda *a, **kw: mock_executor_instance,
    )

    from src.main_app.jobs.backends.thread_backend import _runner

    _runner(
        job_id=job_id,
        user=user,
        cancel_event=event,
        flask_app=flask_app,
    )
    mock_executor_instance.run.assert_called_once_with(job_id, user=user, cancel_event=event)


def test_runner_passes_none_args_by_default(monkeypatch: pytest.MonkeyPatch):
    """Test that _runner passes user=None to JobExecutor when no user given."""
    job_id = 790
    user = None
    event = threading.Event()
    flask_app = MagicMock()

    register_cancel_event(job_id, event)

    mock_executor_instance = MagicMock()
    mock_executor_instance.run.return_value = 0

    monkeypatch.setattr(
        "src.main_app.jobs.job_executor.JobExecutor",
        lambda *a, **kw: mock_executor_instance,
    )

    from src.main_app.jobs.backends.thread_backend import _runner

    _runner(
        job_id=job_id,
        user=user,
        cancel_event=event,
        flask_app=flask_app,
    )
    mock_executor_instance.run.assert_called_once_with(job_id, user=None, cancel_event=event)


def test_start_job_param(mock_jobs_worker_services):
    """Test that start passes args to the backend."""
    mock_job = JobRecord(id=10, job_type="collect_templates_data", status="pending")
    mock_job_data = JobData(job_type="collect_templates_data", job_name="Test", job_class=MagicMock())
    mock_backend = MagicMock()

    from src.main_app.jobs.jobs_lifetime.job_creator import CreatedJob

    mock_jobs_worker_services["create"].return_value = CreatedJob(job=mock_job, job_data=mock_job_data, payload={})
    mock_jobs_worker_services["get_backend"].return_value = mock_backend

    args = {"update_all": "true"}
    job_id = JobStarter().start({"username": "22"}, "collect_templates_data", args=args)

    assert job_id == 10
    mock_jobs_worker_services["create"].assert_called_once()
    # Verify args were passed to creator
    call_kwargs = mock_jobs_worker_services["create"].call_args
    assert call_kwargs[1]["args"] == args or call_kwargs.kwargs.get("args") == args


def test_start_job_without_args_passes_none(mock_jobs_worker_services):
    """Test that start passes args=None when no args given."""
    mock_job = JobRecord(id=11, job_type="collect_templates_data", status="pending")
    mock_job_data = JobData(job_type="collect_templates_data", job_name="Test", job_class=MagicMock())
    mock_backend = MagicMock()

    from src.main_app.jobs.jobs_lifetime.job_creator import CreatedJob

    mock_jobs_worker_services["create"].return_value = CreatedJob(job=mock_job, job_data=mock_job_data, payload={})
    mock_jobs_worker_services["get_backend"].return_value = mock_backend

    job_id = JobStarter().start({"username": "22"}, "collect_templates_data")

    assert job_id == 11
    mock_jobs_worker_services["create"].assert_called_once()
    # Verify args=None was passed to creator
    call_kwargs = mock_jobs_worker_services["create"].call_args
    assert call_kwargs[1].get("args") is None or call_kwargs.kwargs.get("args") is None


def test_start_job_alias_works(mock_jobs_worker_services):
    """Test that start with positional args behaves identically."""
    mock_job = JobRecord(id=12, job_type="collect_templates_data", status="pending")
    mock_job_data = JobData(job_type="collect_templates_data", job_name="Test", job_class=MagicMock())
    mock_backend = MagicMock()

    from src.main_app.jobs.jobs_lifetime.job_creator import CreatedJob

    mock_jobs_worker_services["create"].return_value = CreatedJob(job=mock_job, job_data=mock_job_data, payload={})
    mock_jobs_worker_services["get_backend"].return_value = mock_backend

    args = {"update_all": "true"}
    user = {"username": "alias_user"}
    job_id = JobStarter().start(user, "collect_templates_data", args)

    assert job_id == 12
    mock_jobs_worker_services["create"].assert_called_once()
    mock_backend.start.assert_called_once()
