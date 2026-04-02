"""Worker module for collecting main files for templates."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from ..services import jobs_service
from .workers_list import jobs_targets

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
) -> None:
    try:
        target_func(task_id, user, cancel_event=cancel_event)
    finally:
        _pop_cancel_event(task_id)


def _runner_with_args(
    task_id: int,
    title: str,
    args: Dict[str, Any] | None,
    user: Dict[str, Any] | None,
    cancel_event: threading.Event,
    target_func: Any,
) -> None:
    try:
        target_func(task_id, title, args, user, cancel_event=cancel_event)
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
    db_cancelled = jobs_service.cancel_job(task_id, job_type)
    if db_cancelled:
        logger.info(f"Database cancellation requested for job {task_id}")

    return local_cancelled or db_cancelled


def start_job(user: Dict[str, Any] | None, job_type: str) -> int:
    """
    Start a background job to fix nested tags in all template main files.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
    """
    if job_type not in jobs_targets:
        raise ValueError(f"Unknown job type: {job_type}")

    username = user.get("username") if user else None

    # Create job record
    job = jobs_service.create_job(job_type, username)

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    # Start background thread
    thread = threading.Thread(
        target=_runner,
        args=(job.id, user, cancel_event, jobs_targets[job_type]),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started background job {job.id} for {job_type}")

    return job.id


def start_job_with_args(user: Dict[str, Any] | None, job_type: str, args: Dict[str, Any]) -> int:
    """
    Start a background job with the provided arguments.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
    """
    if job_type not in jobs_targets:
        raise ValueError(f"Unknown job type: {job_type}")

    username = user.get("username") if user else None

    # Create job record
    job = jobs_service.create_job(job_type, username)

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)
    title = args.get("title", "")

    # Start background thread
    thread = threading.Thread(
        target=_runner_with_args,
        args=(job.id, title, args, user, cancel_event, jobs_targets[job_type]),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started background job {job.id} for {job_type}")

    return job.id


__all__ = [
    "start_job",
    "start_job_with_args",
    "cancel_job",
]
