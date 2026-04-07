"""Service for copying SVG languages (translations)."""

from __future__ import annotations

import logging
import threading
from typing import Any

from ...jobs_workers.jobs_worker import _register_cancel_event, _runner, get_jobs_cancel_event
from ...services import jobs_service
from .worker import copy_svg_langs_worker_entry

logger = logging.getLogger(__name__)


def start_copy_svg_langs_job(
    args: Any,
    user: dict[str, Any] | None = None,
) -> int:
    """
    Start a background job to copy SVG translations.

    Args:
        args: Job arguments.
        user: User authentication data.

    Returns:
        Job ID.
    """
    title = args.get("title", "")
    username = user.get("username") if user else None
    job = jobs_service.create_job("copy_svg_langs", username)

    cancel_event = threading.Event()
    _register_cancel_event(job.id, cancel_event)

    thread = threading.Thread(
        target=_runner,
        args=(job.id, args, user, cancel_event, copy_svg_langs_worker_entry),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started copy_svg_langs job {job.id} for {title}")
    return job.id


def get_cancel_event(job_id: int | str):
    return get_jobs_cancel_event(job_id)


__all__ = [
    "get_cancel_event",
    "start_copy_svg_langs_job",
]
