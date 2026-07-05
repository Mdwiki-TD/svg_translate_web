"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import CropMainFilesWorker

logger = logging.getLogger(__name__)


def crop_main_files_worker_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """
    Entry point for crop newest world files background job.

    Args:
        job_id: The job ID
        user: User authentication data for OAuth uploads
        cancel_event: Threading event for cancellation
        args: Optional arguments dict (unused, for unified signature)
    """
    worker = CropMainFilesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "crop_main_files_worker_entry",
]
