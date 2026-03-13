"""
Background job definitions and registry.
"""

from __future__ import annotations
import sys
from pathlib import Path

if _path_ := Path(__file__).parent.parent:
    sys.path.append(str(_path_))

from datetime import datetime
import logging
from typing import Any, Dict

from src.main_app import template_service
from src.main_app.utils.wikitext.titles_utils.last_world_file import find_last_world_file_from_owidslidersrcs
from src.main_app.utils.wikitext.titles_utils import find_main_title
from src.main_app.api_services.category import get_category_members
from src.main_app.api_services.text_bot import get_wikitext


logger = logging.getLogger(__name__)


class MainFilesWorker:
    """Worker for collecting main files for templates."""

    def __init__(self):
        """Return the initial result structure."""
        self.job_id = 0
        self.result = {
            "job_id": 0,
            "started_at": datetime.now().isoformat(),
            "templates_added": [],
            "templates_processed": [],
            "templates_updated": [],
            "templates_failed": [],
            "templates_skipped": [],
            "summary": {
                "total": 0,
                "added": 0,
                "updated": 0,
                "failed": 0,
                "skipped": 0,
                "already_had_main_file": 0,
            },
        }

    def _fetch_and_add_new_templates(self) -> int:
        """
        Fetch templates from the category and add new ones to the database.

        Returns:
            Number of new templates added
        """
        logger.info(f"Job {self.job_id}: Fetching templates from category")

        # Get templates from category
        category_templates = get_category_members("Category:Pages using gadget owidslider")
        logger.info(f"Job {self.job_id}: Found {len(category_templates)} templates in category")

        if not category_templates:
            return 0

        # Get existing template titles
        existing_templates = template_service.list_templates()
        existing_titles = {t.title for t in existing_templates}

        # Find new templates
        new_templates = [t for t in category_templates if t not in existing_titles]
        logger.info(f"Job {self.job_id}: Found {len(new_templates)} new templates to add")

        added_count = 0
        timestamp = datetime.now().isoformat()
        for title in new_templates:
            try:
                # Add template with empty main files
                template_service.add_template(title, "", "")
                self.result["templates_added"].append(
                    {
                        "title": title,
                        "timestamp": timestamp,
                    }
                )
                added_count += 1
                logger.info(f"Job {self.job_id}: Added new template: {title}")
            except ValueError as e:
                # Template already exists (race condition)
                logger.debug(f"Job {self.job_id}: Template {title} already exists: {e}")
            except Exception as e:
                logger.exception(f"Job {self.job_id}: Failed to add template {title}")
                self.result["templates_failed"].append(
                    {
                        "title": title,
                        "timestamp": timestamp,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "context": "adding_new_template",
                    }
                )

        return added_count

    def process(self) -> Dict[str, Any]:
        """Execute the collection processing logic."""

        # Step 1: Fetch new templates from category and add them
        added_count = self._fetch_and_add_new_templates()
        self.result["summary"]["added"] = added_count

        # Step 2: Get all templates (including newly added)
        templates = template_service.list_templates()
        self.result["summary"]["total"] = len(templates)
        self.result["summary"]["already_had_main_file"] = len(
            [t for t in templates if t.main_file and t.last_world_file]
        )

        templates_to_process = [t for t in templates if not (t.main_file and t.last_world_file)]
        logger.info(f"Job {self.job_id}: Found {len(templates)} templates, {len(templates_to_process)} need processing")

        for n, template in enumerate(templates_to_process, start=1):

            logger.info(f"Job {self.job_id}: Processing template {n}/{len(templates_to_process)}: {template.title}")
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
                    self.result["templates_failed"].append(template_info)
                    self.result["summary"]["failed"] += 1
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
                    self.result["templates_failed"].append(template_info)
                    self.result["summary"]["failed"] += 1
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
                self.result["templates_updated"].append(template_info)
                self.result["summary"]["updated"] += 1

            except Exception as e:
                template_info["status"] = "failed"
                template_info["reason"] = f"Exception: {str(e)}"
                template_info["error_type"] = type(e).__name__
                self.result["templates_failed"].append(template_info)
                self.result["summary"]["failed"] += 1
                logger.exception(f"Job {self.job_id}: Error processing template {template.title}")

        # Update summary skipped count
        self.result["summary"]["skipped"] = len(self.result["templates_skipped"])

        logger.info(
            f"Job {self.job_id} completed: {self.result['summary']['updated']} updated, "
            f"{self.result['summary']['failed']} failed, "
            f"{self.result['summary']['skipped']} skipped"
        )

        return self.result

    def run(self) -> Dict[str, Any]:
        """Run the job."""
        self.process()


def start(
) -> None:
    logger.info("Starting collect main files offline job.")
    worker = MainFilesWorker()
    worker.run()


if __name__ == "__main__":
    start()
