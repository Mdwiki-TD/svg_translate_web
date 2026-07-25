"""Unit tests for src/main_app/jobs_workers/jobs_worker.py."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from flask import Flask

from src.main_app.jobs_workers.jobs_worker import (
    _get_jobs_cancel_event,
    _pop_cancel_event,
    _register_cancel_event,
    _runner,
    cancel_job_worker,
    start_job,
)


def test_cancel_event_management():
    job_id = 999
    event = threading.Event()

    _register_cancel_event(job_id, event)
    assert _get_jobs_cancel_event(job_id) is event

    popped = _pop_cancel_event(job_id)
    assert popped is event
    assert _get_jobs_cancel_event(job_id) is None


def test_runner():
    job_id = 1
    user = {"username": "test"}
    cancel_event = threading.Event()
    target_func = MagicMock()
    src = Flask(__name__)
    args = {"foo": "bar"}

    _register_cancel_event(job_id, cancel_event)

    _runner(job_id, user, cancel_event, target_func, src, args)

    target_func.assert_called_once_with(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    assert _get_jobs_cancel_event(job_id) is None


@patch("src.main_app.jobs_workers.jobs_worker.JobsService.cancel_job_db")
@patch("src.main_app.jobs_workers.jobs_worker.create_job_cancelled_file")
def test_cancel_job_worker(mock_create_file, mock_cancel_db):
    job_id = 123
    event = threading.Event()
    _register_cancel_event(job_id, event)

    job = MagicMock()
    job.result_file = "some_file"

    mock_cancel_db.return_value = True

    result = cancel_job_worker(job_id, "test_job", job)

    assert result is True
    assert event.is_set()
    mock_create_file.assert_called_once_with("some_file.cancelled")
    mock_cancel_db.assert_called_once_with(job_id, "test_job")


@patch("src.main_app.jobs_workers.jobs_worker.JobsService.create_job")
@patch("src.main_app.jobs_workers.jobs_worker.jobs_data_public")
@patch("threading.Thread")
def test_start_job(mock_thread, mock_jobs_data, mock_create_job, mock_app):
    with mock_app.app_context():
        user = {"username": "test_user"}
        job_type = "test_type"

        mock_job_data = MagicMock()
        mock_job_data.job_callable = MagicMock()
        mock_jobs_data.get.return_value = mock_job_data

        mock_job_record = MagicMock()
        mock_job_record.id = 456
        mock_create_job.return_value = mock_job_record

        job_id = start_job(user, job_type, {"arg": 1})

        assert job_id == 456
        mock_thread.assert_called_once()
        assert _get_jobs_cancel_event(456) is not None
