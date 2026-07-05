"""
Worker module for rename_owid_pages.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import RenameOwidPagesWorker

logger = logging.getLogger(__name__)


def rename_owid_pages_for_templates(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point.

    Args:
        job_id: The job ID
        user: User authentication data
        cancel_event: Threading event for cancellation
        args: Optional arguments dict (unused, for unified signature)
    """
    logger.info("Starting job %s: rename OWID pages (capitalize first letter)", job_id)
    worker = RenameOwidPagesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "rename_owid_pages_for_templates",
]
