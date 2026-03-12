"""
Worker module for create_owid_pages.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

from ..base_worker import BaseJobWorker
from .process import process_create_owid_pages

logger = logging.getLogger(__name__)


class CreateOwidPagesWorker(BaseJobWorker):
    """Worker for create_owid_pages."""

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "create_owid_pages"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "pages_created": [],
            "pages_processed": [],
            "pages_updated": [],
            "pages_failed": [],
            "pages_skipped": [],
            "summary": {
            },
        }

    def process(self) -> Dict[str, Any]:
        """Execute the collection processing logic."""
        return process_create_owid_pages(
            self.job_id,
            self.result,
            self.user,
            cancel_event=self.cancel_event,
        )


def create_owid_pages_for_templates(
    job_id: int,
    user: Dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Background worker
    """
    logger.info(f"Starting job {job_id}: collect main files for templates")
    worker = CreateOwidPagesWorker(job_id, user, cancel_event)
    worker.run()


__all__ = [
    "create_owid_pages_for_templates",
    "CreateOwidPagesWorker",
]
