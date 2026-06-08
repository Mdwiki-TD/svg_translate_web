"""Worker module for managing background jobs."""

from __future__ import annotations

import logging
import threading
from typing import Any

from flask import Flask, current_app

from ..db.exceptions import DuplicateJobError
from ..db.models import JobRecord
from ..db.services import (
    cancel_job_db,
    create_job,
    get_all_settings_ready,
)
from ..su_services.jobs_files_service import create_job_cancelled_file
from .admin_jobs_workers.workers_list import JobData, jobs_data
from .public_jobs_workers.workers_list_public import jobs_data_public

logger = logging.getLogger(__name__)


JOBS_CANCEL_EVENTS: dict[int, threading.Event] = {}
JOBS_CANCEL_EVENTS_LOCK = threading.Lock()


def _register_cancel_event(job_id: int, cancel_event: threading.Event) -> None:
    with JOBS_CANCEL_EVENTS_LOCK:
        JOBS_CANCEL_EVENTS[job_id] = cancel_event


def _pop_cancel_event(job_id: int) -> threading.Event | None:
    with JOBS_CANCEL_EVENTS_LOCK:
        return JOBS_CANCEL_EVENTS.pop(job_id, None)


def _get_jobs_cancel_event(job_id: int) -> threading.Event | None:
    with JOBS_CANCEL_EVENTS_LOCK:
        return JOBS_CANCEL_EVENTS.get(job_id)


def _load_job_args(job_args) -> dict:
    settings_ready = get_all_settings_ready()
    _args = {}
    for x in job_args:
        arg_value = settings_ready.get(x)
        if arg_value is not None:
            _args[x] = arg_value

    return _args


def _runner(
    job_id: int,
    user: dict[str, Any] | None,
    cancel_event: threading.Event,
    target_func: Any,
    flask_app: Flask,
    args: dict[str, Any] | None = None,
) -> None:
    """
    args=(job.id, user, cancel_event, target_func, flask_app, args),
    """
    with flask_app.app_context():
        try:
            target_func(
                job_id=job_id,
                user=user,
                cancel_event=cancel_event,
                args=args,
            )
        finally:
            _pop_cancel_event(job_id)


def cancel_job_worker(job_id: int, job_type: str | None = None, job: JobRecord | None = None) -> bool:
    """
    Cancel a running job.
    Works across multiple processes by updating the database status.
    Returns True if the job was found and cancellation was requested.
    """
    # 1. Try local cancellation (if the job is in this process)
    cancel_event = _get_jobs_cancel_event(job_id)
    local_cancelled = False
    if cancel_event:
        cancel_event.set()
        logger.info(f"Local cancellation requested for job {job_id}")
        local_cancelled = True

    cancelled_file = False
    # 2. Create result_file_cancelled file
    if job and job.result_file:
        cancelled_file = create_job_cancelled_file(f"{job.result_file}.cancelled")

    # 3. Persist cancellation to DB (for cross-process detection)
    db_cancelled = cancel_job_db(job_id, job_type)
    if db_cancelled:
        logger.info(f"Database cancellation requested for job {job_id}")

    return local_cancelled or cancelled_file or db_cancelled


def start_job(
    user: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
) -> int:
    """
    Start a background job.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
        job_type: The type of job to start
        args: Optional arguments to pass to the worker
    """
    job_data: JobData = jobs_data.get(job_type) or jobs_data_public.get(job_type)
    target_func = job_data.job_callable if job_data else None

    if not target_func:
        raise ValueError(f"Unknown job type: {job_type}")

    username = user.get("username") if user else None
    if not username:
        raise ValueError("User authentication data is required")

    resolved_args = _load_job_args(job_data.job_args) if job_data.job_args else {}
    if args:
        resolved_args.update(args)

    try:
        # Create job record
        job = create_job(job_type, username)
    except DuplicateJobError:
        logger.warning("Attempted to start duplicate job of type '%s' by user '%s'", job_type, username)
        raise
    except Exception as e:
        logger.exception(f"Failed to create job record for job type {job_type}")
        raise e

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    # Capture the Flask app for the background thread (requires app context)
    flask_app = current_app._get_current_object()

    # Start background thread
    thread = threading.Thread(
        target=_runner,
        args=(job.id, user, cancel_event, target_func, flask_app, resolved_args),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started background job {job.id} for {job_type}")

    return job.id


def start_job_cli(
    user: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
    app: Flask | None = None,
) -> int:
    """
    Start a background job.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
        job_type: The type of job to start
        args: Optional arguments to pass to the worker
    """
    job_data: JobData = jobs_data.get(job_type) or jobs_data_public.get(job_type)
    target_func = job_data.job_callable if job_data else None

    if not target_func:
        raise ValueError(f"Unknown job type: {job_type}")

    username = user.get("username") if user else None
    if not username:
        raise ValueError("User authentication data is required")

    resolved_args = _load_job_args(job_data.job_args) if job_data.job_args else {}
    if args:
        resolved_args.update(args)

    try:
        # Create job record
        job = create_job(job_type, username)
    except DuplicateJobError:
        logger.warning("Attempted to start duplicate job of type '%s' by user '%s'", job_type, username)
        raise
    except Exception as e:
        logger.exception(f"Failed to create job record for job type {job_type}")
        raise e

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    # Capture the Flask app for the background thread (requires app context)
    flask_app = app or current_app._get_current_object()

    # Start background thread
    thread = threading.Thread(
        target=_runner,
        args=(job.id, user, cancel_event, target_func, flask_app, resolved_args),
    )
    thread.start()

    logger.info(f"Started background job {job.id} for {job_type}")

    return job.id


__all__ = [
    "start_job",
    "cancel_job_worker",
]
