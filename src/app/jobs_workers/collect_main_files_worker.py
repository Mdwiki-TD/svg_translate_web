"""
Worker module for collecting main files for templates.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any

from .. import template_service
from .. import jobs_service
from ..tasks.texts.text_bot import get_wikitext
from ..tasks.titles.utils.main_file import find_main_title

logger = logging.getLogger("svg_translate")


def process_templates(
    job_id, result: dict[str, list[dict]], result_file: str, cancel_event: threading.Event | None = None
) -> dict[str, list[dict]]:
    # Update job status to running
    try:
        jobs_service.update_job_status(job_id, "running", result_file, job_type="collect_main_files")
    except LookupError:
        logger.warning(f"Job {job_id}: Could not update status to running, job record might have been deleted.")
        return result

    # Get all templates
    templates = template_service.list_templates()
    result["summary"]["total"] = len(templates)
    result["summary"]["already_had_main_file"] = len([t for t in templates if t.main_file])

    templates_to_process = [t for t in templates if not t.main_file]
    logger.info(f"Job {job_id}: Found {len(templates)} templates")

    for n, template in enumerate(templates_to_process, start=1):
        if cancel_event and cancel_event.is_set():
            logger.info(f"Job {job_id}: Cancellation detected, stopping.")
            result["status"] = "cancelled"
            result["cancelled_at"] = datetime.now().isoformat()
            break

        # save progress after check for cancellation
        if n == 1 or n % 10 == 0:
            # Save result to JSON file
            jobs_service.save_job_result_by_name(result_file, result)

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

    # Update summary skipped count
    result["summary"]["skipped"] = len(result["templates_skipped"])
    result["completed_at"] = datetime.now().isoformat()

    # Save result to JSON file
    jobs_service.save_job_result_by_name(result_file, result)

    # Update job status to completed or cancelled
    final_status = "completed"
    if result.get("status") == "cancelled":
        final_status = "cancelled"

    try:
        jobs_service.update_job_status(job_id, final_status, result_file, job_type="collect_main_files")
    except LookupError:
        logger.warning(f"Job {job_id}: Could not update status to {final_status}, job record might have been deleted.")

    logger.info(
        f"Job {job_id} {final_status}: {result['summary']['updated']} updated, "
        f"{result['summary']['failed']} failed, "
        f"{result['summary']['skipped']} skipped"
    )
    return result


def collect_main_files_for_templates(
    job_id: int, user: Any | None = None, cancel_event: threading.Event | None = None
) -> None:
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
        result = process_templates(job_id, result, result_file, cancel_event=cancel_event)
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
            jobs_service.update_job_status(job_id, "failed", result_file, job_type="collect_main_files")
        except LookupError:
            logger.warning(f"Job {job_id}: Could not update status to failed, job record might have been deleted.")
        except Exception:
            logger.exception(f"Job {job_id}: Failed to save error result")
            try:
                jobs_service.update_job_status(job_id, "failed", job_type="collect_main_files")
            except LookupError:
                pass


__all__ = [
    "collect_main_files_for_templates",
]
