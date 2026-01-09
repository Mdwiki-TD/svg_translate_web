"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

from pathlib import Path
import logging
import tempfile
from datetime import datetime
from typing import Any

from ..app_routes.fix_nested.fix_utils import download_svg_file, detect_nested_tags, fix_nested_tags, verify_fix, upload_fixed_svg

from .. import template_service
from .. import jobs_service

logger = logging.getLogger("svg_translate")


def fix_nested_file(
    filename: str,
    user,
) -> dict:
    """High-level orchestration for fixing nested SVG tags.

    Args:
        filename: Name of the SVG file to fix
        user: User object for authentication during upload
    """
    # Use temp directory for processing
    temp_dir = Path(tempfile.mkdtemp())

    download = download_svg_file(filename, temp_dir)
    if not download["ok"]:

        return {
            "success": False,
            "message": f"Failed to download file: {filename}",
            "details": download,
        }

    file_path = download["path"]

    detect_before = detect_nested_tags(file_path)

    if detect_before["count"] == 0:
        return {
            "success": False,
            "message": f"No nested tags found in {filename}",
            "details": {"nested_count": 0},
        }

    if not fix_nested_tags(file_path):
        return {
            "success": False,
            "message": f"Failed to fix nested tags in {filename}",
            "details": {"nested_count": detect_before["count"]},
        }

    verify = verify_fix(file_path, detect_before["count"])

    if verify["fixed"] == 0:
        return {
            "success": False,
            "message": f"No nested tags were fixed in {filename}",
            "details": verify,
        }

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


def process_templates(job_id, user, result: dict[str, list[dict]], result_file: str) -> dict[str, list[dict]]:
    # Update job status to running
    jobs_service.update_job_status(job_id, "running", result_file)

    # Get all templates
    templates = template_service.list_templates()
    result["summary"]["total"] = len(templates)

    logger.info(f"Job {job_id}: Found {len(templates)} templates")

    for n, template in enumerate(templates, start=1):
        logger.info(f"Job {job_id}: Processing template {n}/{len(templates)}: {template.title}")
        template_info = {
            "id": template.id,
            "title": template.title,
            "main_file": template.main_file,
            "timestamp": datetime.now().isoformat(),
        }

        # Skip if template doesn't have a main_file
        if not template.main_file:
            template_info["status"] = "skipped"
            template_info["reason"] = "No main_file set"
            result["templates_skipped"].append(template_info)
            result["summary"]["no_main_file"] += 1
            continue

        try:
            # Run fix_nested process on the main file
            logger.info(
                f"Job {job_id}: Processing {template.main_file} "
                f"for template {template.title}"
            )

            # Process without task_id and db_store since we're tracking in the job
            fix_result = fix_nested_file(
                filename=template.main_file,
                user=user,
            )
            nested_count = fix_result.get("details", {}).get("nested_count", 0)

            if fix_result["success"]:
                template_info["status"] = "success"
                template_info["fix_result"] = fix_result
                result["templates_success"].append(template_info)
                result["summary"]["success"] += 1
                logger.info(
                    f"Job {job_id}: Successfully processed {template.main_file}"
                )
            elif nested_count == 0:
                template_info["status"] = "skipped"
                template_info["reason"] = "No nested tags found"
                template_info["fix_result"] = fix_result
                result["templates_skipped"].append(template_info)
                result["summary"]["skipped"] += 1
                logger.info(
                    f"Job {job_id}: No nested tags found in {template.main_file}"
                )
            else:
                template_info["status"] = "failed"
                template_info["reason"] = fix_result.get("message", "Unknown error")
                template_info["fix_result"] = fix_result
                result["templates_failed"].append(template_info)
                result["summary"]["failed"] += 1
                logger.warning(
                    f"Job {job_id}: Failed to process {template.main_file}: "
                    f"{fix_result.get('message')}"
                )

        except Exception as e:
            template_info["status"] = "failed"
            template_info["reason"] = f"Exception: {str(e)}"
            template_info["error_type"] = type(e).__name__
            result["templates_failed"].append(template_info)
            result["summary"]["failed"] += 1
            logger.exception(f"Job {job_id}: Error processing template {template.title}")

        if n == 1 or n % 10 == 0:
            # Save result to JSON file
            jobs_service.save_job_result_by_name(result_file, result)

    # Update summary skipped count
    result["summary"]["skipped"] = len(result["templates_skipped"])
    result["completed_at"] = datetime.now().isoformat()

    # Save result to JSON file
    jobs_service.save_job_result_by_name(result_file, result)

    # Update job status to completed
    jobs_service.update_job_status(job_id, "completed", result_file)

    logger.info(
        f"Job {job_id} completed: {result['summary']['success']} successful, "
        f"{result['summary']['failed']} failed, "
        f"{result['summary']['skipped']} skipped"
    )

    return result


def fix_nested_main_files_for_templates(job_id: int, user: Any | None) -> None:
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
    result_file = jobs_service.generate_result_file_name(job_id, job_type)
    try:
        result = process_templates(job_id, user, result, result_file)

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
            jobs_service.update_job_status(job_id, "failed", result_file)
        except Exception:
            logger.exception(f"Job {job_id}: Failed to save error result")
            jobs_service.update_job_status(job_id, "failed")


__all__ = [
    "fix_nested_main_files_for_templates",
]
