"""Unit tests for jobs_worker.py logic."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.db.exceptions import DuplicateJobError
from src.main_app.jobs_workers.jobs_worker import (
    _load_job_args,
    _pop_cancel_event,
    _register_cancel_event,
    _runner,
    cancel_job_worker,
    start_job,
    start_job_cli,
)


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    return app


@pytest.fixture
def mock_db_services(monkeypatch: pytest.MonkeyPatch):
    mocks = {
        "create": MagicMock(),
        "cancel_db": MagicMock(),
        "settings": MagicMock(),
        "cancel_file": MagicMock(),
    }
    monkeypatch.setattr("src.main_app.jobs_workers.jobs_worker.create_job", mocks["create"])
    monkeypatch.setattr("src.main_app.jobs_workers.jobs_worker.cancel_job_db", mocks["cancel_db"])
    monkeypatch.setattr("src.main_app.jobs_workers.jobs_worker.get_all_settings_ready", mocks["settings"])
    monkeypatch.setattr("src.main_app.jobs_workers.jobs_worker.create_job_cancelled_file", mocks["cancel_file"])
    return mocks


def test_register_pop_cancel_event():
    event = threading.Event()
    _register_cancel_event(999, event)
    assert _pop_cancel_event(999) is event
    assert _pop_cancel_event(999) is None


def test_load_job_args(mock_db_services):
    mock_db_services["settings"].return_value = {"arg1": "val1", "arg2": "val2"}
    args = _load_job_args(
        [
            {"key": "arg1", "as": "arg1"},
            {"key": "missing", "as": "missing"},
        ]
    )
    assert args == {"arg1": "val1"}


def test_runner(flask_app):
    target = MagicMock()
    cancel_event = threading.Event()
    _register_cancel_event(1, cancel_event)

    _runner(1, {"user": "test"}, cancel_event, target, flask_app, {"a": 1})

    target.assert_called_once_with(job_id=1, user={"user": "test"}, cancel_event=cancel_event, args={"a": 1})
    assert _pop_cancel_event(1) is None  # should be popped


def test_cancel_job_worker(mock_db_services):
    event = threading.Event()
    _register_cancel_event(1, event)
    job = MagicMock()
    job.result_file = "test_result"

    mock_db_services["cancel_db"].return_value = True
    mock_db_services["cancel_file"].return_value = True

    res = cancel_job_worker(1, "test_type", job)

    assert res is True
    assert event.is_set()
    mock_db_services["cancel_db"].assert_called_once_with(1, "test_type")
    mock_db_services["cancel_file"].assert_called_once_with("test_result.cancelled")


class TestStartJob:
    @patch(
        "src.main_app.jobs_workers.jobs_worker.jobs_data_admins",
        {"test": MagicMock(job_callable=lambda **kwargs: None, job_args=[])},
    )
    def test_start_job_success(self, mock_db_services, flask_app):
        mock_db_services["create"].return_value = MagicMock(id=123)
        user = {"username": "testuser"}

        with flask_app.app_context():
            job_id = start_job(user, "test")
            assert job_id == 123

    def test_start_job_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown job type"):
            start_job({"username": "u"}, "unknown")

    def test_start_job_no_username(self, mock_db_services):
        with patch("src.main_app.jobs_workers.jobs_worker.jobs_data_admins", {"test": MagicMock()}):
            with pytest.raises(ValueError, match="User authentication data is required"):
                start_job({}, "test")

    @patch(
        "src.main_app.jobs_workers.jobs_worker.jobs_data_admins",
        {"test": MagicMock(job_callable=lambda **kwargs: None, job_args=[])},
    )
    def test_start_job_duplicate(self, mock_db_services, flask_app):
        mock_db_services["create"].side_effect = DuplicateJobError()
        with flask_app.app_context():
            with pytest.raises(DuplicateJobError):
                start_job({"username": "u"}, "test")

    @patch(
        "src.main_app.jobs_workers.jobs_worker.jobs_data_admins",
        {"test": MagicMock(job_callable=lambda **kwargs: None, job_args=[])},
    )
    def test_start_job_cli_success(self, mock_db_services, flask_app):
        mock_db_services["create"].return_value = MagicMock(id=456)
        user = {"username": "testuser"}

        job_id = start_job_cli(user, "test", app=flask_app)
        assert job_id == 456
