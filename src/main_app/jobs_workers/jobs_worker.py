"""Worker module for collecting main files for templates."""

from __future__ import annotations

import logging
import threading
from typing import Any

from . import jobs_service
from .collect_main_files_worker import collect_main_files_for_templates
from .crop_main_files import crop_main_files_for_templates
from .download_main_files_worker import download_main_files_for_templates
from .fix_nested_main_files_worker import fix_nested_main_files_for_templates

logger = logging.getLogger("svg_translate")


CANCEL_EVENTS: dict[int, threading.Event] = {}
CANCEL_EVENTS_LOCK = threading.Lock()


def _register_cancel_event(job_id: int, cancel_event: threading.Event) -> None:
    with CANCEL_EVENTS_LOCK:
        CANCEL_EVENTS[job_id] = cancel_event


def _pop_cancel_event(job_id: int) -> threading.Event | None:
    with CANCEL_EVENTS_LOCK:
        return CANCEL_EVENTS.pop(job_id, None)


def get_jobs_cancel_event(job_id: int) -> threading.Event | None:
    with CANCEL_EVENTS_LOCK:
        return CANCEL_EVENTS.get(job_id)


def _runner(job_id: int, user: Any | None, cancel_event: threading.Event, target_func: Any) -> None:
    try:
        target_func(job_id, user, cancel_event=cancel_event)
    finally:
        _pop_cancel_event(job_id)


def cancel_job(job_id: int) -> bool:
    """
    Cancel a running job.
    Returns True if a cancel event was found and set, False otherwise.
    """
    cancel_event = get_jobs_cancel_event(job_id)
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
        "crop_main_files": crop_main_files_for_templates,
        "download_main_files": download_main_files_for_templates,
    }
    if job_type not in jobs_targets:
        raise ValueError(f"Unknown job type: {job_type}")
    # Create job record
    job = jobs_service.create_job(job_type)

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


__all__ = [
    "start_job",
    "cancel_job",
]
