"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import mwclient
import requests

from ... import template_service
from ...config import settings
from ...utils.wiki_client import get_user_site
from ...utils.commons_client import create_commons_session
from .. import jobs_service
from .api import get_file_text, update_file_text
from .crop_file import crop_svg_file
from .download import download_file_for_cropping
from .upload import upload_cropped_file
from .utils import generate_cropped_filename
from .wikitext import create_cropped_file_text, update_original_file_text

logger = logging.getLogger(__name__)


def upload_one(
    job_id: int,
    file_info: dict[str, Any],
    site: mwclient.Site | None,
    result: dict[str, Any],
) -> None:
    original_file = file_info["original_file"]
    cropped_filename = file_info["cropped_filename"]
    cropped_path = file_info.get("cropped_path")

    if not cropped_path:
        return

    wikitext = get_file_text(original_file, site)
    cropped_file_wikitext = create_cropped_file_text(original_file, wikitext)

    # Step 4: Upload cropped file to Commons
    upload_result = upload_cropped_file(
        cropped_filename,
        cropped_path,
        site,
        cropped_file_wikitext,
    )

    if not upload_result["success"]:
        file_info["status"] = "failed"
        file_info["reason"] = "upload_failed"
        file_info["error"] = upload_result.get("error", "Unknown upload error")
        result["summary"]["failed"] += 1
        logger.warning(f"Job {job_id}: Failed to upload {cropped_filename}")
        return

    file_info["status"] = "uploaded"
    result["summary"]["uploaded"] += 1
    logger.info(f"Job {job_id}: Successfully uploaded {cropped_filename}")

    # Step 5: Update original file wikitext to link to cropped version
    updated_file_text = update_original_file_text(cropped_filename, wikitext)
    if wikitext == updated_file_text:
        logger.info(f"Job {job_id}: No update needed for original file text of {original_file}")
        return

    update_text = update_file_text(original_file, updated_file_text, site)

    if not update_text["success"]:
        error = update_text.get("error", "Unknown error")
        logger.warning(f"Job {job_id}: Failed to update original file text for {original_file} (reason: {error})")


def process_one(
    job_id: int,
    template: template_service.TemplateRecord,
    result: dict[str, Any],
    original_dir: Path,
    cropped_dir: Path,
    session: requests.Session,
):

    file_info = {
        "template_id": template.id,
        "template_title": template.title,
        "original_file": template.last_world_file,
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "cropped_filename": None,
        "reason": None,
        "error": None,
    }

    # Step 1: Download the original file
    try:
        download_result = download_file_for_cropping(
            template.last_world_file,
            original_dir,
            session=session,
        )

    except Exception as e:
        file_info["status"] = "failed"
        file_info["reason"] = "exception"
        file_info["error"] = f"{type(e).__name__}: {str(e)}"

        result["summary"]["failed"] += 1
        logger.exception(f"Job {job_id}: Exception processing {template.last_world_file}")
        return file_info

    if not download_result["success"]:
        file_info["status"] = "failed"
        file_info["reason"] = "download_failed"
        file_info["error"] = download_result.get("error", "Unknown download error")

        result["summary"]["failed"] += 1
        logger.warning(f"Job {job_id}: Failed to download {template.last_world_file}")
        return file_info

    downloaded_path = download_result["path"]
    result["summary"]["processed"] += 1

    # Step 2: Crop the SVG (placeholder)
    cropped_filename = generate_cropped_filename(template.last_world_file)
    cropped_output_path = cropped_dir / Path(cropped_filename.removeprefix("File:")).name

    crop_result = crop_svg_file(downloaded_path, cropped_output_path)

    if not crop_result["success"]:
        file_info["status"] = "failed"
        file_info["reason"] = "crop_failed"
        file_info["error"] = crop_result.get("error", "Unknown crop error")

        result["summary"]["failed"] += 1
        logger.warning(f"Job {job_id}: Failed to crop {template.last_world_file}")
        return file_info

    file_info["cropped_path"] = cropped_output_path

    result["summary"]["cropped"] += 1

    # Step 3: Generate cropped filename
    file_info["cropped_filename"] = cropped_filename

    return file_info


def process_crops(
    job_id: int,
    result: dict[str, Any],
    result_file: str,
    user: Dict[str, Any] | None,
    cancel_event: threading.Event | None = None,
    upload_files: bool = False,
) -> dict[str, Any]:
    """
    Process cropping for all templates.

    Args:
        job_id: The job ID
        result: The result dictionary to populate
        result_file: The result file name
        user: User authentication data for OAuth uploads
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
    templates_with_files = [t for t in templates if t.last_world_file]

    # Apply development mode limit from settings
    dev_limit = settings.download.dev_limit
    if dev_limit > 0 and len(templates_with_files) > dev_limit:
        logger.info(
            f"Job {job_id}: Development mode - limiting crop from " f"{len(templates_with_files)} to {dev_limit} files"
        )
        templates_with_files = templates_with_files[:dev_limit]

    result["summary"]["total"] = len(templates_with_files)
    logger.info(f"Job {job_id}: Found {len(templates_with_files)} templates with main files")

    # Create a shared session for all downloads
    session = create_commons_session(settings.oauth.user_agent)

    # Process each template
    original_dir = Path(settings.paths.crop_main_files_path) / "original"
    cropped_dir = Path(settings.paths.crop_main_files_path) / "cropped"

    # Get user site for upload
    site = get_user_site(user)

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
            original_dir,
            cropped_dir,
            session,
        )
        status = file_info["status"]
        if status == "failed":
            logger.warning(
                f"Job {job_id}: Failed to process {template.last_world_file} (reason: {file_info['reason']})"
            )
            result["files_processed"].append(file_info)
            continue

        cropped_filename = file_info.get("cropped_filename")

        if not user:
            # No user provided, skip upload
            file_info["status"] = "skipped"
            file_info["reason"] = "no_user_auth"
            result["summary"]["skipped"] += 1
            logger.info(f"Job {job_id}: Skipped upload for {cropped_filename} (no user auth)")
            result["files_processed"].append(file_info)
            continue

        if not upload_files:
            file_info["status"] = "skipped"
            file_info["reason"] = "upload disabled"
            result["summary"]["skipped"] += 1
            logger.info(f"Job {job_id}: Skipped upload for {cropped_filename} (upload disabled)")
            result["files_processed"].append(file_info)
            continue

        # Upload the file
        upload_one(
            job_id,
            file_info,
            site,
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
