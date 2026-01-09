"""Worker module for collecting main files for templates."""

from __future__ import annotations

import logging
import threading
from typing import Any

from . import jobs_service
from .jobs_workers.collect_main_files_worker import collect_main_files_for_templates
from .jobs_workers.fix_nested_main_files_worker import fix_nested_main_files_for_templates

logger = logging.getLogger("svg_translate")


CANCEL_EVENTS: dict[int, threading.Event] = {}
CANCEL_EVENTS_LOCK = threading.Lock()


def _register_cancel_event(job_id: int, cancel_event: threading.Event) -> None:
    with CANCEL_EVENTS_LOCK:
        CANCEL_EVENTS[job_id] = cancel_event


def _pop_cancel_event(job_id: int) -> threading.Event | None:
    with CANCEL_EVENTS_LOCK:
        return CANCEL_EVENTS.pop(job_id, None)


def get_cancel_event(job_id: int) -> threading.Event | None:
    with CANCEL_EVENTS_LOCK:
        return CANCEL_EVENTS.get(job_id)


def cancel_job(job_id: int) -> bool:
    """
    Cancel a running job.
    Returns True if a cancel event was found and set, False otherwise.
    """
    cancel_event = get_cancel_event(job_id)
    if cancel_event:
        cancel_event.set()
        logger.info(f"Cancellation requested for job {job_id}")
        return True
    return False


def start_job(user: Any | None, job_type: str) -> int:
    """
    Start a background job to fix nested tags in all template main files.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
    """
    jobs_targets = {
        "fix_nested_main_files": fix_nested_main_files_for_templates,
        "collect_main_files": collect_main_files_for_templates,
    }
    if job_type not in jobs_targets:
        raise ValueError(f"Unknown job type: {job_type}")
    # Create job record
    job = jobs_service.create_job(job_type)

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    def _runner(job_id: int, user: Any | None, cancel_event: threading.Event) -> None:
        try:
            jobs_targets[job_type](job_id, user, cancel_event=cancel_event)
        finally:
            _pop_cancel_event(job_id)

    # Start background thread
    thread = threading.Thread(
        target=_runner,
        args=(job.id, user, cancel_event),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started background job {job.id} for {job_type}")

    return job.id


def start_collect_main_files_job(user: Any | None=None) -> int:
    """
    Start a background job to collect main files for templates.
    Returns the job ID.
    """
    return start_job(user, "collect_main_files")


def start_fix_nested_main_files_job(user: Any | None) -> int:
    """
    Start a background job to fix nested tags in all template main files.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
    """
    return start_job(user, "fix_nested_main_files")


__all__ = [
    "collect_main_files_for_templates",
    "start_collect_main_files_job",
    "fix_nested_main_files_for_templates",
    "start_fix_nested_main_files_job",
    "cancel_job",
]
