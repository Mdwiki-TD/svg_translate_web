"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from ... import template_service
from ...config import settings
from ...utils.commons_client import create_commons_session
from .. import jobs_service
from .crop_file import crop_svg_file
from .upload import upload_cropped_file
from .download import download_file_for_cropping
from .utils import generate_cropped_filename

logger = logging.getLogger("svg_translate")


def upload_one(
    job_id,
    file_info,
    user,
    crop_box,
    result,
):

    cropped_filename = file_info["cropped_file"]
    cropped_path = file_info["output_path"]

    if cropped_path:
        # Step 4: Upload cropped file to Commons
        upload_result = upload_cropped_file(
            cropped_filename,
            cropped_path,
            user,
            crop_box,
        )

        if upload_result["success"]:
            file_info["status"] = "uploaded"
            result["summary"]["uploaded"] += 1
            logger.info(f"Job {job_id}: Successfully uploaded {cropped_filename}")
        else:
            file_info["status"] = "failed"
            file_info["reason"] = "upload_failed"
            file_info["error"] = upload_result.get("error", "Unknown upload error")
            result["summary"]["failed"] += 1
            logger.warning(f"Job {job_id}: Failed to upload {cropped_filename}")


def process_one(
    job_id,
    template,
    result,
    temp_dir,
    session,
    crop_box,
):

    file_info = {
        "template_id": template.id,
        "template_title": template.title,
        "original_file": template.main_file,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "cropped_file": None,
        "reason": None,
        "error": None,
    }

    # Step 1: Download the original file
    try:
        download_result = download_file_for_cropping(
            template.main_file,
            temp_dir,
            session=session,
        )

    except Exception as e:
        file_info["status"] = "failed"
        file_info["reason"] = "exception"
        file_info["error"] = f"{type(e).__name__}: {str(e)}"
        result["files_processed"].append(file_info)
        result["summary"]["failed"] += 1
        logger.exception(f"Job {job_id}: Exception processing {template.main_file}")
        return file_info

    if not download_result["success"]:
        file_info["status"] = "failed"
        file_info["reason"] = "download_failed"
        file_info["error"] = download_result.get("error", "Unknown download error")
        result["files_processed"].append(file_info)
        result["summary"]["failed"] += 1
        logger.warning(f"Job {job_id}: Failed to download {template.main_file}")
        return file_info

    downloaded_path = download_result["path"]
    result["summary"]["processed"] += 1

    # Step 2: Crop the SVG (placeholder)
    crop_result = crop_svg_file(downloaded_path, crop_box)

    if not crop_result["success"]:
        file_info["status"] = "failed"
        file_info["reason"] = "crop_failed"
        file_info["error"] = crop_result.get("error", "Unknown crop error")
        result["files_processed"].append(file_info)
        result["summary"]["failed"] += 1
        logger.warning(f"Job {job_id}: Failed to crop {template.main_file}")
        return file_info

    file_info["cropped_path"] = crop_result["output_path"]

    result["summary"]["cropped"] += 1

    # Step 3: Generate cropped filename
    cropped_filename = generate_cropped_filename(template.main_file)
    file_info["cropped_file"] = cropped_filename

    return file_info


def process_crops(
    job_id: int,
    result: dict[str, Any],
    result_file: str,
    user: Any | None,
    crop_box: tuple[float, float, float, float] | None = None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """
    Process cropping for all templates.

    Args:
        job_id: The job ID
        result: The result dictionary to populate
        result_file: The result file name
        user: User authentication data for OAuth uploads
        crop_box: Optional tuple of (x, y, width, height) for cropping
        cancel_event: Optional event to check for cancellation

    Returns:
        The populated result dictionary
    """
    # Update job status to running
    try:
        jobs_service.update_job_status(job_id, "running", result_file, job_type="crop_main_files")
    except LookupError:
        logger.warning(f"Job {job_id}: Could not update status to running, job record might have been deleted.")
        return result

    # Get all templates with main files
    templates = template_service.list_templates()
    templates_with_files = [t for t in templates if t.main_file]

    # Apply development mode limit from settings
    dev_limit = settings.download.dev_limit
    if dev_limit > 0 and len(templates_with_files) > dev_limit:
        logger.info(
            f"Job {job_id}: Development mode - limiting crop from "
            f"{len(templates_with_files)} to {dev_limit} files"
        )
        templates_with_files = templates_with_files[:dev_limit]

    result["summary"]["total"] = len(templates_with_files)
    logger.info(f"Job {job_id}: Found {len(templates_with_files)} templates with main files")

    # Create a shared session for all downloads
    session = create_commons_session(settings.oauth.user_agent)

    # Process each template
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_dir = Path(tmp_dir)

        for n, template in enumerate(templates_with_files, start=1):
            # Check for cancellation
            if cancel_event and cancel_event.is_set():
                logger.info(f"Job {job_id}: Cancellation detected, stopping.")
                result["status"] = "cancelled"
                result["cancelled_at"] = datetime.now().isoformat()
                break

            # Save progress periodically
            if n == 1 or n % 10 == 0:
                jobs_service.save_job_result_by_name(result_file, result)

            logger.info(f"Job {job_id}: Processing {n}/{len(templates_with_files)}: {template.title}")

            file_info = process_one(
                job_id,
                template,
                result,
                temp_dir,
                session,
                user,
                crop_box,
            )

            cropped_filename = file_info["cropped_file"]

            if not user:
                # No user provided, skip upload
                file_info["status"] = "skipped"
                file_info["reason"] = "no_user_auth"
                result["summary"]["skipped"] += 1
                logger.info(f"Job {job_id}: Skipped upload for {cropped_filename} (no user auth)")
                continue

            if cropped_filename:
                upload_one(
                    job_id,
                    file_info,
                    user,
                    crop_box,
                    result,
                )
            result["files_processed"].append(file_info)

    # Mark as completed if not cancelled or failed
    if result.get("status") != "cancelled":
        result["status"] = "completed"
        logger.info(f"Job {job_id}: Crop processing completed")

    return result


__all__ = [
    "process_crops",
]
