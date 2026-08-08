"""
Worker module for create_owid_pages.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import CreateOwidPagesWorker

logger = logging.getLogger(__name__)


def create_owid_pages_for_templates(data: JobsRunner) -> None:
    """
    Background worker
    """
    logger.info("Starting job %s: create OWID pages for templates", data.job_id)

    worker = CreateOwidPagesWorker(data)
    worker.run()


__all__ = [
    "create_owid_pages_for_templates",
]
