"""Service for fixing nested tags in SVG files."""

from __future__ import annotations

import logging
import threading
from typing import Any

from ...jobs_workers.jobs_worker import _register_cancel_event, _runner_with_args, get_jobs_cancel_event
from ...services import jobs_service
from .worker import fix_nested_tasks_worker_entry

logger = logging.getLogger(__name__)


def start_fix_nested_tasks_job(
    args: dict[str, Any],
    user: dict[str, Any] | None = None,
) -> int:
    """
    Start a background job to fix nested tags in SVG files.

    Args:
        args: Job arguments (filename, filenames, upload).
        user: User authentication data.

    Returns:
        Job ID.
    """
    title = args.get("title", "")
    username = user.get("username") if user else None
    job = jobs_service.create_job("fix_nested_tasks", username)

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    thread = threading.Thread(
        target=_runner_with_args,
        args=(job.id, args, user, cancel_event, fix_nested_tasks_worker_entry),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started fix_nested_tasks job {job.id} for {title}")
    return job.id


def get_cancel_event(job_id: int | str):
    """Get the cancel event for a job."""
    return get_jobs_cancel_event(job_id)


__all__ = [
    "get_cancel_event",
    "start_fix_nested_tasks_job",
]
