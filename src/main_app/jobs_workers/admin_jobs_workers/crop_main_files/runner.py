"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import CropMainFilesWorker

logger = logging.getLogger(__name__)


from ...objects import JobsRunner


def crop_main_files_worker_entry(
    data: JobsRunner | None = None,
    *,
    job_id: int | None = None,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> None:
    """
    Entry point for crop newest world files background job.
    """
    if data is not None:
        job_id = data.job_id
        user = data.user
        cancel_event = data.cancel_event
        args = data.args
        form_data = data.form_data

    worker = CropMainFilesWorker(
        job_id=job_id,  # type: ignore
        user=user,      # type: ignore
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "crop_main_files_worker_entry",
]
