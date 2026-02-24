"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from .. import template_service
from ..app_routes.fix_nested.fix_utils import (
    detect_nested_tags,
    download_svg_file,
    fix_nested_tags,
    upload_fixed_svg,
    verify_fix,
)
from . import jobs_service
from .utils import generate_result_file_name

logger = logging.getLogger(__name__)


def repair_nested_svg_tags(
    filename: str,
    user,
    cancel_event: threading.Event | None = None,
) -> dict:
    """High-level orchestration for fixing nested SVG tags.

    Args:
        filename: Name of the SVG file to fix
        user: User object for authentication during upload
    """
    # Use temp directory for processing
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_dir = Path(tmp_dir)

        download = download_svg_file(filename, temp_dir)
        if not download["ok"]:
            return {
                "success": False,
                "message": f"Failed to download file: {filename}",
                "details": download,
            }

        file_path = download["path"]

        if cancel_event and cancel_event.is_set():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        detect_before = detect_nested_tags(file_path)

        if detect_before["count"] == 0:
            return {
                "success": False,
                "message": f"No nested tags found in {filename}",
                "details": {"nested_count": 0},
                "no_nested_tags": True,
            }

        if not fix_nested_tags(file_path):
            return {
                "success": False,
                "message": f"Failed to fix nested tags in {filename}",
                "details": {"nested_count": detect_before["count"]},
            }

        if cancel_event and cancel_event.is_set():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        verify = verify_fix(file_path, detect_before["count"])

        if verify["fixed"] == 0:
            return {
                "success": False,
                "message": f"No nested tags were fixed in {filename}",
                "details": verify,
            }

        if cancel_event and cancel_event.is_set():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        upload = upload_fixed_svg(filename, file_path, verify["fixed"], user)

        if not upload["ok"]:
            return {
                "success": False,
                "message": f"Fixed {verify['fixed']} nested tag(s), but upload failed.",
                "details": {**verify, **upload},
            }

        return {
            "success": True,
            "message": f"Successfully fixed {verify['fixed']} nested tag(s) and uploaded {filename}.",
            "details": {
                **verify,
                "upload_result": upload["result"],
            },
        }


def log_skipped_template_no_main_file(result, template_info) -> None:
    """
    Logs a skipped template due to the absence of a main file.

    Args:
        result: Dictionary tracking the overall processing results.
        template_info: Dictionary containing information about the template.
    """
    template_info["status"] = "skipped"
    template_info["reason"] = "No main_file set"
    result["templates_skipped"].append(template_info)
    result["summary"]["no_main_file"] += 1


def log_skipped_template_no_nested_tags(result, template_info, fix_result) -> None:
    """
    Logs information about a template that was skipped due to having no nested tags.

    Args:
        result: A dictionary tracking the overall job results.
        template_info: A dictionary containing metadata about the template.
        fix_result: A dictionary containing the result of the fix attempt.
    """
    template_info["status"] = "skipped"
    template_info["reason"] = "No nested tags found"
    template_info["fix_result"] = fix_result
    result["templates_skipped"].append(template_info)
    result["summary"]["skipped"] += 1


def log_successful_template_processing(result, template_info, fix_result) -> None:
    """
    Logs a successfully processed template.

    Args:
        result: Dictionary tracking the overall processing results.
        template_info: Dictionary containing information about the template.
        fix_result: Dictionary containing the results of the fix operation.
    """
    template_info["status"] = "success"
    template_info["fix_result"] = fix_result
    result["templates_success"].append(template_info)
    result["summary"]["success"] += 1


def log_template_failure(result, template_info, e) -> None:
    """
    Logs a template processing failure due to an exception.

    Args:
        result: A dictionary tracking the overall job results.
        template_info: A dictionary containing metadata about the template.
        e: The exception that caused the failure.
    """
    template_info["status"] = "failed"
    template_info["reason"] = f"Exception: {str(e)}"
    template_info["error_type"] = type(e).__name__
    result["templates_failed"].append(template_info)
    result["summary"]["failed"] += 1


def log_failed_template(result, template_info, fix_result) -> None:
    """
    Logs a template that failed during processing.

    Args:
        result: A dictionary tracking the overall job results.
        template_info: A dictionary containing metadata about the template.
        fix_result: A dictionary containing the result of the fix attempt.
    """
    template_info["status"] = "failed"
    template_info["reason"] = fix_result.get("message", "Unknown error")
    template_info["fix_result"] = fix_result
    result["templates_failed"].append(template_info)
    result["summary"]["failed"] += 1


def process_templates(
    job_id,
    user,
    result: dict[str, list[dict]],
    result_file: str,
    cancel_event: threading.Event | None = None,
) -> dict[str, list[dict]]:
    # Update job status to running
    try:
        jobs_service.update_job_status(job_id, "running", result_file, job_type="fix_nested_main_files")
    except LookupError:
        logger.warning(f"Job {job_id}: Could not update status to running, job record might have been deleted.")
        return result

    # Get all templates
    templates = template_service.list_templates()
    result["summary"]["total"] = len(templates)

    logger.info(f"Job {job_id}: Found {len(templates)} templates")

    for n, template in enumerate(templates, start=1):
        logger.info(f"Job {job_id}: Processing template {n}/{len(templates)}: {template.title}")

        if cancel_event and cancel_event.is_set():
            logger.info(f"Job {job_id}: Cancellation detected, stopping.")
            result["status"] = "cancelled"
            result["cancelled_at"] = datetime.now().isoformat()
            break

        # Save progress after check for cancellation
        if n == 1 or n % 10 == 0:
            # Save result to JSON file
            jobs_service.save_job_result_by_name(result_file, result)

        template_info = {
            "id": template.id,
            "title": template.title,
            "main_file": template.main_file,
            "timestamp": datetime.now().isoformat(),
        }

        # Skip if template doesn't have a main_file
        if not template.main_file:
            log_skipped_template_no_main_file(result, template_info)
            continue

        fix_result = {}
        try:
            # Process without task_id and db_store since we're tracking in the job
            fix_result = repair_nested_svg_tags(
                filename=template.main_file,
                user=user,
                cancel_event=cancel_event,
            )

        except Exception as e:
            log_template_failure(result, template_info, e)
            logger.exception(f"Job {job_id}: Error processing template {template.title}")
            continue

        if fix_result.get("cancelled"):
            logger.info(f"Job {job_id}: Cancellation detected, stopping.")
            result["status"] = "cancelled"
            result["cancelled_at"] = datetime.now().isoformat()
            break

        if fix_result["success"]:
            log_successful_template_processing(result, template_info, fix_result)
            logger.info(f"Job {job_id}: Successfully processed {template.main_file}")

        elif fix_result.get("no_nested_tags", False):
            log_skipped_template_no_nested_tags(result, template_info, fix_result)
            logger.info(f"Job {job_id}: No nested tags found in {template.main_file}")

        else:
            log_failed_template(result, template_info, fix_result)
            logger.warning(f"Job {job_id}: Failed to process {template.main_file}: " f"{fix_result.get('message')}")

    # Update summary skipped count
    result["summary"]["skipped"] = len(result["templates_skipped"])
    result["completed_at"] = datetime.now().isoformat()

    # Save result to JSON file
    jobs_service.save_job_result_by_name(result_file, result)

    # Update job status to completed or cancelled
    final_status = "cancelled" if result.get("status") == "cancelled" else "completed"

    try:
        jobs_service.update_job_status(job_id, final_status, result_file, job_type="fix_nested_main_files")
    except LookupError:
        logger.warning(f"Job {job_id}: Could not update status to {final_status}, job record might have been deleted.")

    logger.info(
        f"Job {job_id} {final_status}: {result['summary']['success']} successful, "
        f"{result['summary']['failed']} failed, "
        f"{result['summary']['skipped']} skipped"
    )

    return result


def fix_nested_main_files_for_templates(
    job_id: int, user: Any | None, cancel_event: threading.Event | None = None
) -> None:
    """
    Background worker to run fix_nested task on all main files from templates.

    This function:
    1. Fetches all templates from the database
    2. For each template with a main_file:
       - Runs the fix_nested process (download, fix, upload)
       - Uses the user's OAuth credentials for file uploads
    3. Saves a detailed report to a JSON file
    """
    job_type = "fix_nested_main_files"

    logger.info(f"Starting job {job_id}: fix nested tags for template main files")

    # Initialize result tracking early to avoid NameError in exception handler
    result = {
        "job_id": job_id,
        "started_at": datetime.now().isoformat(),
        "templates_processed": [],
        "templates_success": [],
        "templates_failed": [],
        "templates_skipped": [],
        "summary": {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "no_main_file": 0,
        },
    }
    result_file = generate_result_file_name(job_id, job_type)
    try:
        result = process_templates(job_id, user, result, result_file, cancel_event=cancel_event)

    except Exception as e:
        logger.exception(f"Job {job_id}: Fatal error during execution")

        # Save error result
        error_result = {
            "job_id": job_id,
            "started_at": result.get("started_at", datetime.now().isoformat()),
            "completed_at": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__,
        }

        try:
            jobs_service.save_job_result_by_name(result_file, error_result)
            jobs_service.update_job_status(job_id, "failed", result_file, job_type="fix_nested_main_files")
        except LookupError:
            logger.warning(f"Job {job_id}: Could not update status to failed, job record might have been deleted.")
        except Exception:
            logger.exception(f"Job {job_id}: Failed to save error result")
            try:
                jobs_service.update_job_status(job_id, "failed", job_type="fix_nested_main_files")
            except LookupError:
                pass


__all__ = [
    "fix_nested_main_files_for_templates",
]
