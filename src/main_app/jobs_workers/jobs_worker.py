"""Worker module for managing background jobs."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from flask import Flask, current_app

from ..db.services import cancel_job as cancel_job_db
from ..db.services import (
    create_job,
)
from .workers_list import jobs_targets, jobs_targets_public

logger = logging.getLogger(__name__)


JOBS_CANCEL_EVENTS: dict[int, threading.Event] = {}
JOBS_CANCEL_EVENTS_LOCK = threading.Lock()


def _register_cancel_event(task_id: int, cancel_event: threading.Event) -> None:
    with JOBS_CANCEL_EVENTS_LOCK:
        JOBS_CANCEL_EVENTS[task_id] = cancel_event


def _pop_cancel_event(task_id: int) -> threading.Event | None:
    with JOBS_CANCEL_EVENTS_LOCK:
        return JOBS_CANCEL_EVENTS.pop(task_id, None)


def get_jobs_cancel_event(task_id: int) -> threading.Event | None:
    with JOBS_CANCEL_EVENTS_LOCK:
        return JOBS_CANCEL_EVENTS.get(task_id)


def _runner(
    task_id: int,
    user: Dict[str, Any] | None,
    cancel_event: threading.Event,
    target_func: Any,
    flask_app: Flask,
    args: Dict[str, Any] | None = None,
) -> None:
    with flask_app.app_context():
        try:
            target_func(task_id, user, cancel_event=cancel_event, args=args)
        finally:
            _pop_cancel_event(task_id)


def cancel_job(task_id: int, job_type: str | None = None) -> bool:
    """
    Cancel a running job.
    Works across multiple processes by updating the database status.
    Returns True if the job was found and cancellation was requested.
    """
    # 1. Try local cancellation (if the job is in this process)
    cancel_event = get_jobs_cancel_event(task_id)
    local_cancelled = False
    if cancel_event:
        cancel_event.set()
        logger.info(f"Local cancellation requested for job {task_id}")
        local_cancelled = True

    # 2. Persist cancellation to DB (for cross-process detection)
    db_cancelled = cancel_job_db(task_id, job_type)
    if db_cancelled:
        logger.info(f"Database cancellation requested for job {task_id}")

    return local_cancelled or db_cancelled


def start_job(user: Dict[str, Any] | None, job_type: str, args: Dict[str, Any] | None = None) -> int:
    """
    Start a background job.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
        job_type: The type of job to start
        args: Optional arguments to pass to the worker
    """
    job_func = jobs_targets.get(job_type) or jobs_targets_public.get(job_type)
    if not job_func:
        raise ValueError(f"Unknown job type: {job_type}")

    username = user.get("username") if user else None

    # Create job record
    job = create_job(job_type, username)

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    # Capture the Flask app for the background thread (requires app context)
    flask_app = current_app._get_current_object()

    # Start background thread
    thread = threading.Thread(
        target=_runner,
        args=(job.id, user, cancel_event, job_func, flask_app, args),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started background job {job.id} for {job_type}")

    return job.id


# Keep backward-compatible alias
start_job_with_args = start_job


__all__ = [
    "start_job",
    "start_job_with_args",
    "cancel_job",
]
