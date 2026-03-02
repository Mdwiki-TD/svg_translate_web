"""
Worker module for collecting main files for templates.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

from .. import template_service
from ..api_services.text_bot import get_wikitext
from ..utils.wikitext.titles_utils import find_last_world_file_from_owidslidersrcs, find_main_title
from .base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


class CollectMainFilesWorker(BaseJobWorker):
    """Worker for collecting main files for templates."""

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "collect_main_files"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "job_id": self.job_id,
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

    def process(self) -> Dict[str, Any]:
        """Execute the collection processing logic."""
        result = self.result

        # Get all templates
        templates = template_service.list_templates()
        result["summary"]["total"] = len(templates)
        result["summary"]["already_had_main_file"] = len(
            [t for t in templates if t.main_file and t.last_world_file]
        )

        templates_to_process = [t for t in templates if not (t.main_file and t.last_world_file)]
        logger.info(f"Job {self.job_id}: Found {len(templates)} templates")

        for n, template in enumerate(templates_to_process, start=1):
            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                break

            # Save progress after check for cancellation
            if n == 1 or n % 10 == 0:
                self._save_progress()

            logger.info(
                f"Job {self.job_id}: Processing template {n}/{len(templates_to_process)}: {template.title}"
            )
            template_info = {
                "id": template.id,
                "title": template.title,
                "original_main_file": template.main_file,
                "timestamp": datetime.now().isoformat(),
                "new_main_file": "",
                "last_world_file": "",
            }
            try:
                # Fetch wikitext from Commons
                logger.info(f"Job {self.job_id}: Fetching wikitext for {template.title}")
                wikitext = get_wikitext(template.title, project="commons.wikimedia.org")

                if not wikitext:
                    template_info["status"] = "failed"
                    template_info["reason"] = "Could not fetch wikitext from Commons"
                    result["templates_failed"].append(template_info)
                    result["summary"]["failed"] += 1
                    logger.warning(f"Job {self.job_id}: Could not fetch wikitext for {template.title}")
                    continue

                # Extract main file using find_main_title
                main_file = find_main_title(wikitext)
                if main_file:
                    template_info["new_main_file"] = main_file

                last_world_file = find_last_world_file_from_owidslidersrcs(wikitext)
                if last_world_file:
                    template_info["last_world_file"] = last_world_file

                if not main_file and not last_world_file:
                    template_info["status"] = "failed"
                    template_info["reason"] = "Could not find main file or last world file in wikitext"
                    template_info["wikitext_length"] = len(wikitext)
                    result["templates_failed"].append(template_info)
                    result["summary"]["failed"] += 1
                    logger.warning(
                        f"Job {self.job_id}: Could not find main file or last world file for {template.title}"
                    )
                    continue

                # Update template with main file
                logger.info(
                    f"Job {self.job_id}: Updating {template.title} with main_file: {main_file} "
                    f"and last_world_file: {last_world_file}"
                )

                template_service.update_template_if_not_none(
                    template.id,
                    template.title,
                    main_file,
                    last_world_file,
                )

                template_info["status"] = "updated"
                result["templates_updated"].append(template_info)
                result["summary"]["updated"] += 1

            except Exception as e:
                template_info["status"] = "failed"
                template_info["reason"] = f"Exception: {str(e)}"
                template_info["error_type"] = type(e).__name__
                result["templates_failed"].append(template_info)
                result["summary"]["failed"] += 1
                logger.exception(f"Job {self.job_id}: Error processing template {template.title}")

        # Update summary skipped count
        result["summary"]["skipped"] = len(result["templates_skipped"])

        logger.info(
            f"Job {self.job_id} completed: {result['summary']['updated']} updated, "
            f"{result['summary']['failed']} failed, "
            f"{result['summary']['skipped']} skipped"
        )

        return result

    def _save_progress(self) -> None:
        """Save current progress to result file."""
        from . import jobs_service

        try:
            jobs_service.save_job_result_by_name(self.result_file, self.result)
        except Exception:
            logger.exception(f"Job {self.job_id}: Failed to save progress")


def collect_main_files_for_templates(
    job_id: int,
    user: Dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
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
    worker = CollectMainFilesWorker(job_id, user, cancel_event)
    worker.run()


__all__ = [
    "collect_main_files_for_templates",
    "CollectMainFilesWorker",
]
