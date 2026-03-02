"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

from ...config import settings
from ..base_worker import BaseJobWorker
from .process_new import process_crops

logger = logging.getLogger(__name__)


class CropMainFilesWorker(BaseJobWorker):
    """Worker for cropping main files and uploading them with (cropped) suffix."""

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "crop_main_files"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

    def before_run(self) -> bool:
        """Skip status update as process_crops handles it internally."""
        # process_crops handles its own status updates, so we just return True
        return True

    def process(self) -> Dict[str, Any]:
        """Execute the crop processing logic."""
        return process_crops(
            self.job_id,
            self.result,
            self.result_file,
            self.user,
            cancel_event=self.cancel_event,
            upload_files=settings.dynamic.get("upload_cropped_files", False),
        )


def crop_main_files_for_templates(
    job_id: int,
    user: Dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Entry point for crop newest world files background job.

    Args:
        job_id: The job ID
        user: User authentication data for OAuth uploads
        cancel_event: Threading event for cancellation
    """
    worker = CropMainFilesWorker(job_id, user, cancel_event)
    worker.run()


__all__ = [
    "crop_main_files_for_templates",
    "CropMainFilesWorker",
]
