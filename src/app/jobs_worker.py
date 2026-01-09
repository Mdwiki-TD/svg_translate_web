"""Worker module for collecting main files for templates."""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any

from . import template_service
from . import jobs_service
from .tasks.texts.text_bot import get_wikitext
from .tasks.titles.utils.main_file import find_main_title
from .app_routes.fix_nested.fix_utils import process_fix_nested

logger = logging.getLogger("svg_translate")


def collect_main_files_for_templates(job_id: int, user: Any | None=None) -> None:
    """
    Background worker to collect main files for templates that don't have one.

    This function:
    1. Fetches all templates from the database
    2. For each template without a main_file:
       - Fetches the wikitext from Commons
       - Extracts the main file using find_main_title
       - Updates the template in the database
    3. Saves a detailed report to a JSON file
    """
    logger.info(f"Starting job {job_id}: collect main files for templates")
    job_type = "collect_main_files"
    # Initialize result tracking early to avoid NameError in exception handler
    result = {
        "job_id": job_id,
        "started_at": datetime.now().isoformat(),
        "templates_processed": [],
        "templates_updated": [],
        "templates_failed": [],
        "templates_skipped": [],
        "summary": {
            "total": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0,
            "already_had_main_file": 0,
        },
    }
    result_file = jobs_service.generate_result_file_name(job_id, job_type)
    try:
        # Update job status to running
        jobs_service.update_job_status(job_id, "running", result_file)

        # Get all templates
        templates = template_service.list_templates()
        result["summary"]["total"] = len(templates)
        already_had_main_file = [t for t in templates if t.main_file]
        result["summary"]["already_had_main_file"] = len(already_had_main_file)
        templates_to_process = [t for t in templates if not t.main_file]
        logger.info(f"Job {job_id}: Found {len(templates)} templates")

        for n, template in enumerate(templates_to_process, start=1):
            logger.info(f"Job {job_id}: Processing template {n}/{len(templates_to_process)}: {template.title}")
            template_info = {
                "id": template.id,
                "title": template.title,
                "original_main_file": template.main_file,
                "timestamp": datetime.now().isoformat(),
            }
            try:
                # Fetch wikitext from Commons
                logger.info(f"Job {job_id}: Fetching wikitext for {template.title}")
                wikitext = get_wikitext(template.title, project="commons.wikimedia.org")

                if not wikitext:
                    template_info["status"] = "failed"
                    template_info["reason"] = "Could not fetch wikitext from Commons"
                    result["templates_failed"].append(template_info)
                    result["summary"]["failed"] += 1
                    logger.warning(f"Job {job_id}: Could not fetch wikitext for {template.title}")
                    continue

                # Extract main file using find_main_title
                main_file = find_main_title(wikitext)

                if not main_file:
                    template_info["status"] = "failed"
                    template_info["reason"] = "Could not find main file in wikitext"
                    template_info["wikitext_length"] = len(wikitext)
                    result["templates_failed"].append(template_info)
                    result["summary"]["failed"] += 1
                    logger.warning(f"Job {job_id}: Could not find main file for {template.title}")
                    continue

                # Update template with main file
                logger.info(f"Job {job_id}: Updating {template.title} with main_file: {main_file}")
                template_service.update_template(template.id, template.title, main_file)

                template_info["status"] = "updated"
                template_info["new_main_file"] = main_file
                result["templates_updated"].append(template_info)
                result["summary"]["updated"] += 1

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
            f"Job {job_id} completed: {result['summary']['updated']} updated, "
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
                # Extract username from user object - handle both dict and object types
                username = None
                if user:
                    if isinstance(user, dict):
                        username = user.get("username")
                    else:
                        username = getattr(user, "username", None)

                fix_result = process_fix_nested(
                    filename=template.main_file,
                    user=user,
                    task_id=None,  # Don't create individual task records
                    username=username,
                    db_store=None,  # Don't use fix_nested task store
                )

                if fix_result["success"]:
                    template_info["status"] = "success"
                    template_info["fix_result"] = fix_result
                    result["templates_success"].append(template_info)
                    result["summary"]["success"] += 1
                    logger.info(
                        f"Job {job_id}: Successfully processed {template.main_file}"
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


def start_job(user: Any | None, job_type: str) -> int:
    """
    Start a background job to fix nested tags in all template main files.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
    """
    jobs_targets = {
        "fix_nested_main_files": fix_nested_main_files_for_templates,
        "collect_main_files": collect_main_files_for_templates,
    }
    if job_type not in jobs_targets:
        raise ValueError(f"Unknown job type: {job_type}")
    # Create job record
    job = jobs_service.create_job(job_type)
    # Start background thread
    thread = threading.Thread(
        target=jobs_targets[job_type],
        args=(job.id, user),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started background job {job.id} for {job_type}")

    return job.id


def start_collect_main_files_job(user: Any | None=None) -> int:
    """
    Start a background job to collect main files for templates.
    Returns the job ID.
    """
    return start_job(user, "collect_main_files")


def start_fix_nested_main_files_job(user: Any | None) -> int:
    """
    Start a background job to fix nested tags in all template main files.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
    """
    return start_job(user, "fix_nested_main_files")


__all__ = [
    "collect_main_files_for_templates",
    "start_collect_main_files_job",
    "fix_nested_main_files_for_templates",
    "start_fix_nested_main_files_job",
]
