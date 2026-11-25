"""Unit tests for jobs_worker.py logic."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest
from flask import Flask
from src.main_app.database.exceptions import DuplicateRecordError
from src.main_app.jobs.backends.thread_backend import _runner
from src.main_app.jobs.backends.thread_cancel_registry import (
    pop_cancel_event,
    register_cancel_event,
)
from src.main_app.jobs.jobs_lifetime.job_creator import _load_job_args
from src.main_app.jobs.jobs_lifetime.jobs_canceller import JobCanceller
from src.main_app.jobs.jobs_lifetime.jobs_starter import JobStarter


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    return app


@pytest.fixture
def mock_jobs_service() -> MagicMock:
    """Fake JobsService, injected directly into JobStarter / JobCanceller."""
    return MagicMock()


@pytest.fixture
def mock_jobs_files_service() -> MagicMock:
    """Fake JobFilesService, injected directly into JobCanceller."""
    return MagicMock()


@pytest.fixture
def mock_db_services(monkeypatch: pytest.MonkeyPatch):
    mocks = {
        "settings": MagicMock(),
        "backend": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.jobs.jobs_lifetime.job_creator.SettingsService.get_all_settings_ready",
        mocks["settings"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs.jobs_lifetime.jobs_starter.BackendRegistry.get_backend",
        lambda *a: mocks["backend"],
    )
    return mocks


def test_register_pop_cancel_event():
    event = threading.Event()
    register_cancel_event(999, event)
    assert pop_cancel_event(999) is event
    assert pop_cancel_event(999) is None


def test_load_job_args(mock_db_services):
    mock_db_services["settings"].return_value = {"arg1": "val1", "arg2": "val2"}
    args = _load_job_args(
        [
            {"key": "arg1", "as": "arg1"},
            {"key": "missing", "as": "missing"},
        ]
    )
    assert args == {"arg1": "val1"}


def test_runner(flask_app, monkeypatch: pytest.MonkeyPatch):
    cancel_event = threading.Event()
    register_cancel_event(1, cancel_event)

    mock_executor_instance = MagicMock()
    mock_executor_instance.run.return_value = 0
    monkeypatch.setattr(
        "src.main_app.jobs.job_executor.JobExecutor",
        lambda *a, **kw: mock_executor_instance,
    )

    _runner(
        job_id=1,
        user={"user": "test"},
        cancel_event=cancel_event,
        flask_app=flask_app,
    )

    mock_executor_instance.run.assert_called_once_with(1, user={"user": "test"}, cancel_event=cancel_event)
    assert pop_cancel_event(1) is None  # should be popped


def test_runner_no_form_data(flask_app, monkeypatch: pytest.MonkeyPatch):
    cancel_event = threading.Event()
    register_cancel_event(1, cancel_event)

    mock_executor_instance = MagicMock()
    mock_executor_instance.run.return_value = 0
    monkeypatch.setattr(
        "src.main_app.jobs.job_executor.JobExecutor",
        lambda *a, **kw: mock_executor_instance,
    )

    _runner(
        job_id=1,
        user={"user": "test"},
        cancel_event=cancel_event,
        flask_app=flask_app,
    )

    mock_executor_instance.run.assert_called_once_with(1, user={"user": "test"}, cancel_event=cancel_event)
    assert pop_cancel_event(1) is None  # should be popped


def test_cancel_job_worker(mock_jobs_service, mock_jobs_files_service):
    event = threading.Event()
    register_cancel_event(1, event)
    job = MagicMock()
    job.id = 1
    job.result_file = "test_result"
    job.job_type = "test_type"
    job.backend = "thread"

    mock_jobs_service.cancel_job_db.return_value = True
    mock_jobs_service.get_by.return_value = job
    mock_jobs_files_service.create_cancel_file.return_value = True

    # Use the real ThreadBackend so cancel() sets the in-process event
    from src.main_app.jobs.backends.thread_backend import ThreadBackend

    mock_backend_registry = MagicMock()
    mock_backend_registry.get_backend.return_value = ThreadBackend()

    res = JobCanceller(
        jobs_files_service=mock_jobs_files_service,
        jobs_service=mock_jobs_service,
        backend_registry=mock_backend_registry,
    ).cancel(1, "test_type", job)

    assert res is True
    assert event.is_set()
    mock_jobs_service.cancel_job_db.assert_called_once_with(1, "test_type")
    mock_jobs_files_service.create_cancel_file.assert_called_once()


@pytest.fixture
def mock_load_job_data(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    _mock.return_value = MagicMock()
    monkeypatch.setattr("src.main_app.jobs.registry.load_job_data", _mock)
    monkeypatch.setattr("src.main_app.jobs.jobs_lifetime.job_creator.load_job_data", _mock)
    return _mock


class TestStartJob:
    def test_start_job_success(self, mock_db_services, mock_load_job_data, mock_jobs_service, flask_app):
        mock_load_job_data.return_value = MagicMock(job_class=lambda *args, **kwargs: None, job_args=[])
        mock_jobs_service.create_job.return_value = MagicMock(id=123)
        user = {"username": "testuser"}

        with flask_app.app_context():
            job_id = JobStarter(jobs_service=mock_jobs_service).start(user, "test")

        assert job_id == 123
        mock_jobs_service.create_job.assert_called_once()
        mock_jobs_service.save_payload.assert_called_once()

    def test_start_job_cli_success(self, mock_db_services, mock_load_job_data, mock_jobs_service, flask_app):
        mock_load_job_data.return_value = MagicMock(job_class=lambda *args, **kwargs: None, job_args=[])
        mock_jobs_service.create_job.return_value = MagicMock(id=456)
        user = {"username": "testuser"}

        job_id = JobStarter(jobs_service=mock_jobs_service).start(user, "test")
        assert job_id == 456

    def test_start_job_unknown_type(self, mock_jobs_service):
        with pytest.raises(ValueError, match="Unknown job type"):
            JobStarter(jobs_service=mock_jobs_service).start({"username": "u"}, "unknown")

    def test_start_job_no_username(self, mock_load_job_data, mock_jobs_service):
        mock_load_job_data.return_value = MagicMock()
        with pytest.raises(ValueError, match="User authentication data is required"):
            JobStarter(jobs_service=mock_jobs_service).start({}, "test")

    def test_start_job_duplicate(self, mock_db_services, mock_load_job_data, mock_jobs_service, flask_app):
        mock_load_job_data.return_value = MagicMock(job_class=lambda *args, **kwargs: None, job_args=[])
        mock_jobs_service.create_job.side_effect = DuplicateRecordError()
        with flask_app.app_context():
            with pytest.raises(DuplicateRecordError):
                JobStarter(jobs_service=mock_jobs_service).start({"username": "u"}, "test")
