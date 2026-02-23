"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any
from .. import jobs_service
from .process import process_crops

logger = logging.getLogger("svg_translate")


def crop_main_files_for_templates(
    job_id: int,
    user: Any | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Entry point for crop main files background job.

    Args:
        job_id: The job ID
        user: User authentication data for OAuth uploads
        cancel_event: Threading event for cancellation
    """
    job_type = "crop_main_files"
    result_file = jobs_service.generate_result_file_name(job_id, job_type)

    # Initialize result structure
    result: dict[str, Any] = {
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

    try:
        result = process_crops(job_id, result, result_file, user, cancel_event=cancel_event)
    except Exception as e:
        logger.exception(f"Job {job_id}: Error during crop processing")
        result["status"] = "failed"
        result["error"] = str(e)
        result["error_type"] = type(e).__name__

    # Finalize timestamps
    result["completed_at"] = datetime.now().isoformat()
    final_status = result.get("status", "completed")

    # Save final results
    try:
        jobs_service.save_job_result_by_name(result_file, result)
    except Exception:
        logger.exception(f"Job {job_id}: Failed to save job result")

    # Update final status
    try:
        jobs_service.update_job_status(job_id, final_status, result_file, job_type=job_type)
    except LookupError:
        logger.warning(f"Job {job_id}: Could not update final status, job record might have been deleted.")

    logger.info(f"Job {job_id}: Finished with status {final_status}")


__all__ = [
    "crop_main_files_for_templates",
]
