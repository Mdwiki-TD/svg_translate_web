"""
Worker module for copy_svg_translation.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any
from ...jobs_workers.base_worker import BaseJobWorker
from .job import CopySvgLangsProcessor

logger = logging.getLogger(__name__)


class CopySvgLangsWorker(BaseJobWorker):
    """
    Worker for copying SVG translations from a main file to its versions.
    """

    def __init__(
        self,
        job_id: int,
        title: str,
        args: Any,
        user: dict[str, Any] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.title = title
        self.args = args
        super().__init__(job_id, user, cancel_event)

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "copy_svg_langs"

    def get_initial_result(self) -> dict[str, Any]:
        """Return the initial result structure."""
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "title": self.title,
            "stages": {
                "text": {"number": 1, "status": "Pending", "message": "Getting text"},
                "titles": {"number": 2, "status": "Pending", "message": "Getting titles"},
                "translations": {"number": 3, "status": "Pending", "message": "Getting translations"},
                "download": {"number": 4, "status": "Pending", "message": "Downloading files"},
                "nested": {"number": 5, "status": "Pending", "message": "Analyze nested files"},
                "inject": {"number": 6, "status": "Pending", "message": "Injecting translations"},
                "upload": {"number": 7, "status": "Pending", "message": "Uploading files"},
            },
            "summary": {},
        }

    def process(self) -> dict[str, Any]:
        processor = CopySvgLangsProcessor(
            job_id=self.job_id,
            title=self.title,
            args=self.args,
            user=self.user,
            result=self.result,
            result_file=self.result_file,
            cancel_event=self.cancel_event,
        )
        return processor.run()


def copy_svg_langs_worker_entry(
    job_id: int,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    **kwargs: Any,
) -> None:
    """Entry point for the background job."""
    title = kwargs.get("title")
    args = kwargs.get("args")
    if not title or not args:
        logger.error(f"Job {job_id}: Missing title or args")
        return

    worker = CopySvgLangsWorker(
        job_id=job_id,
        title=title,
        args=args,
        user=user,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "copy_svg_langs_worker_entry",
    "CopySvgLangsWorker",
]
