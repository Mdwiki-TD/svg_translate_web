"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from .. import template_service
from .. import jobs_service
from ..app_routes.fix_nested.fix_utils import process_fix_nested

logger = logging.getLogger("svg_translate")


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
    # Extract username from user object - handle both dict and object types
    username = None
    if user:
        if isinstance(user, dict):
            username = user.get("username")
        else:
            username = getattr(user, "username", None)

    result_file = jobs_service.generate_result_file_name(job_id, job_type)
    try:
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
                fix_result = process_fix_nested(
                    filename=template.main_file,
                    user=user,
                    task_id=None,  # Don't create individual task records
                    username=username,
                    db_store=None,  # Don't use fix_nested task store
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
