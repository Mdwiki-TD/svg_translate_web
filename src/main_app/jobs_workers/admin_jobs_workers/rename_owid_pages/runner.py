"""
Worker module for rename_owid_pages.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import RenameOwidPagesWorker

logger = logging.getLogger(__name__)


def rename_owid_pages_for_templates(data: JobsRunner) -> None:
    """Background worker entry-point."""
    logger.info("Starting job %s: rename OWID pages (capitalize first letter)", data.job_id)
    worker = RenameOwidPagesWorker(data)
    worker.run()


__all__ = [
    "rename_owid_pages_for_templates",
]
