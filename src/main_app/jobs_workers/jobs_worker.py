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
from .admin_jobs_workers.workers_list import jobs_data_admins
from .objects import JobData
from .public_jobs_workers.workers_list_public import jobs_data_public

logger = logging.getLogger(__name__)


JOBS_CANCEL_EVENTS: dict[int, threading.Event] = {}
JOBS_CANCEL_EVENTS_LOCK = threading.Lock()


def load_job_data(job_type) -> JobData | None:
    return jobs_data_admins.get(job_type) or jobs_data_public.get(job_type)


def _register_cancel_event(job_id: int, cancel_event: threading.Event) -> None:
    with JOBS_CANCEL_EVENTS_LOCK:
        JOBS_CANCEL_EVENTS[job_id] = cancel_event


def _pop_cancel_event(job_id: int) -> threading.Event | None:
    with JOBS_CANCEL_EVENTS_LOCK:
        return JOBS_CANCEL_EVENTS.pop(job_id, None)


def _get_jobs_cancel_event(job_id: int) -> threading.Event | None:
    with JOBS_CANCEL_EVENTS_LOCK:
        return JOBS_CANCEL_EVENTS.get(job_id)


def _load_job_args(job_args: list[dict[str, str]]) -> dict:
    if not job_args:
        return {}

    settings_ready = get_all_settings_ready()
    _args: dict[str, Any] = {}

    for item in job_args:
        key = item["key"]
        key_as = item["as"]
        arg_value = settings_ready.get(key)
        if arg_value is not None:
            _args[key_as] = arg_value

    return _args


def _runner(
    job_id: int,
    user: dict[str, Any],
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

    cancelled_file = None
    # 2. Create result_file_cancelled file
    if job and job.result_file:
        cancelled_file = create_job_cancelled_file(f"{job.result_file}.cancelled")

    # 3. Persist cancellation to DB (for cross-process detection)
    try:
        db_cancelled = cancel_job_db(job_id, job_type)
        if db_cancelled:
            logger.info(f"Database cancellation requested for job {job_id}")

    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Failed to cancel job %s in database.", job_id)
        db_cancelled = False

    return local_cancelled or cancelled_file is not None or db_cancelled


def _start_job_impl(
    auth_payload: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
    *,
    daemon: bool = False,
    flask_app: Flask | None = None,
) -> int:
    job_data: JobData | None = load_job_data(job_type)
    target_func = job_data.job_callable if job_data else None

    if not job_data or not target_func:
        raise ValueError(f"Unknown job type: {job_type}")

    username = auth_payload.get("username") if auth_payload else None
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
    except Exception:
        logger.exception("Failed to create job record for job type %s", job_type)
        raise

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    resolved_flask_app = flask_app or current_app._get_current_object()  # type: ignore[attr-defined]

    if "csrf_token" in resolved_args:
        del resolved_args["csrf_token"]

    # Start background thread
    thread = threading.Thread(
        target=_runner,
        args=(job.id, auth_payload, cancel_event, target_func, resolved_flask_app, resolved_args),
        daemon=daemon,
    )
    thread.start()

    logger.info("Started background job %s for %s", job.id, job_type)

    return job.id


def start_job(
    auth_payload: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
) -> int:
    """Start a background job as a daemon thread. Returns the job ID."""
    return _start_job_impl(
        auth_payload,
        job_type,
        args,
        daemon=True,
        flask_app=current_app._get_current_object(),  # type: ignore[attr-defined]
    )


def start_job_cli(
    auth_payload: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
    app: Flask | None = None,
) -> int:
    """Start a background job from CLI. Returns the job ID."""
    flask_app = app or current_app._get_current_object()  # type: ignore[attr-defined]
    return _start_job_impl(
        auth_payload,
        job_type,
        args,
        flask_app=flask_app,
    )


__all__ = [
    "start_job",
    "start_job_cli",
    "cancel_job_worker",
]
