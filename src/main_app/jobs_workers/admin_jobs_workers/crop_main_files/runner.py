"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import CropMainFilesWorker

logger = logging.getLogger(__name__)


def crop_main_files_worker_entry(data: JobsRunner) -> None:
    """
    Entry point for crop newest world files background job.
    """
    worker = CropMainFilesWorker(
        job_id=data.job_id,
        user=data.user,
        cancel_event=data.cancel_event,
        args=data.args,
    )
    worker.run()


__all__ = [
    "crop_main_files_worker_entry",
]
