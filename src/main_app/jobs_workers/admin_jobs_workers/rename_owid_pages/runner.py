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
    data: JobsRunner,
) -> None:
    """Background worker entry-point."""
    logger.info("Starting job %s: rename OWID pages (capitalize first letter)", data.job_id)
    worker = RenameOwidPagesWorker(
        job_id=data.job_id,
        user=data.user,
        cancel_event=data.cancel_event,
        args=data.args,
    )
    worker.run()


__all__ = [
    "rename_owid_pages_for_templates",
]
