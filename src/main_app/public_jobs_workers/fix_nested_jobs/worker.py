"""
Worker module for fix_nested_jobs.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

from ...jobs_workers.base_worker import BaseJobWorker
from .job import FixNestedJobsProcessor

logger = logging.getLogger(__name__)


class FixNestedJobsWorker(BaseJobWorker):
    """
    Worker for fixing nested tags in user-submitted SVG files.
    """

    def __init__(
        self,
        job_id: int,
        args: Any,
        user: dict[str, Any] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args
        super().__init__(job_id, user, cancel_event)

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "fix_nested_jobs"

    def get_initial_result(self) -> dict[str, Any]:
        """Return the initial result structure."""
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "filename": None,
            "file_result": {
                "status": "pending",
                "path": None,
                "error": None,
            },
            "stages": {
                "download": {"status": "Pending", "message": "Downloading files"},
                "analyze": {"status": "Pending", "message": "Analyzing nested tags"},
                "fix": {"status": "Pending", "message": "Fixing nested tags"},
                "verify": {"status": "Pending", "message": "Verifying fixes"},
                "upload": {"status": "Pending", "message": "Uploading fixed files"},
            },
        }

    def process(self) -> dict[str, Any]:
        processor = FixNestedJobsProcessor(
            job_id=self.job_id,
            args=self.args,
            user=self.user,
            result=self.result,
            result_file=self.result_file,
            cancel_event=self.cancel_event,
        )
        return processor.run()


# --- main pipeline --------------------------------------------
def fix_nested_jobs_worker_entry(
    job_id: str,
    user: Dict[str, str] | None,
    *,
    cancel_event: threading.Event | None = None,
    args: Any = None,
) -> None:
    """Entry point for the background job."""

    worker = FixNestedJobsWorker(
        job_id=job_id,
        args=args,
        user=user,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "fix_nested_jobs_worker_entry",
    "FixNestedJobsWorker",
]
