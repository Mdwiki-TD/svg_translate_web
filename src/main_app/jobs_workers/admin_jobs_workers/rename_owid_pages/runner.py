"""
Worker module for rename_owid_pages.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import RenameOwidPagesWorker

logger = logging.getLogger(__name__)


from ...objects import JobsRunner


def rename_owid_pages_for_templates(
    data: JobsRunner | None = None,
    *,
    job_id: int | None = None,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    if data is not None:
        job_id = data.job_id
        user = data.user
        cancel_event = data.cancel_event
        args = data.args
        form_data = data.form_data

    logger.info("Starting job %s: rename OWID pages (capitalize first letter)", job_id)
    worker = RenameOwidPagesWorker(
        job_id=job_id,  # type: ignore
        user=user,      # type: ignore
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "rename_owid_pages_for_templates",
]
