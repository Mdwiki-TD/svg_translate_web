"""
Worker module for collecting main files for templates.

"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

import mwclient

from ...api_services.category import get_category_members
from ...api_services.clients import get_user_site
from ...api_services.pages_api import get_page_text
from ...db.services import (
    add_template_data,
    get_chart_by_slug,
    list_templates,
    update_template_data,
)
from ...utils.wikitext import find_template_source
from ...utils.wikitext.titles_utils import (
    find_last_world_file_from_owidslidersrcs,
    find_main_title,
)
from ..base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


@dataclass
class TemplateInfo:
    """
    Holds all state for a single template being processed.
    """

    id: int
    title: str
    new_main_file: str
    last_world_file: str
    source: str
    status: str = "processing"
    error: str | None = None
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "new_main_file": self.new_main_file,
            "last_world_file": self.last_world_file,
            "source": self.source,
            "status": self.status,
        }
        if self.error is not None:
            result["error"] = self.error
        if self.error_type is not None:
            result["error_type"] = self.error_type
        return result


def slugify_title(title: str) -> str:
    """Derive a slug from a template title."""
    # Remove 'Template:OWID/' or 'Template:' prefix
    if title.startswith("Template:OWID/"):
        name = title[len("Template:OWID/") :]
    elif title.startswith("Template:"):
        name = title[len("Template:") :]
    else:
        name = title

    # Lowercase, replace spaces and underscores with hyphens
    slug = name.lower().replace(" ", "-").replace("_", "-")
    # Remove any other non-alphanumeric characters (except hyphens)
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    # Remove multiple hyphens
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")

    if slug:
        # Only assign slug if it exists in the owid_charts table
        try:
            get_chart_by_slug(slug)
            return slug
        except (LookupError, RuntimeError):
            return None
    return None


class CollectMainFilesWorker(BaseJobWorker):
    """Worker for collecting main files for templates."""

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.update_all = False
        self.user = user
        self.site: mwclient.Site | None = None
        if args and str(args.get("update_all", "")).lower() == "true":
            self.update_all = True

        super().__init__(job_id, user, cancel_event)
        self.result: Dict[str, Any] = self.get_initial_result()

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "collect_templates_data"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "pages_processed": [],
            "pages_added": [],
            "pages_updated": [],
            "pages_skipped": [],
            "pages_failed": [],
            "summary": {
                "total": 0,
                "processed": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
            },
        }

    def _fetch_and_add_new_templates(self) -> None:
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
            return

        # Get existing template titles
        existing_templates = list_templates()
        existing_titles = {t.title for t in existing_templates}

        # Find new templates
        new_templates = [t for t in category_templates if t not in existing_titles]
        logger.info(f"Job {self.job_id}: Found {len(new_templates)} new templates to add")

        for n, title in enumerate(new_templates, start=1):
            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected during template addition.")
                break

            tmp_info = TemplateInfo(
                id=n,
                title=title,
                new_main_file="",
                last_world_file="",
                source="",
                status="",
            )
            try:
                add_template_data({"title": title})
                self.result["pages_added"].append(tmp_info.to_dict())
                logger.info(f"Job {self.job_id}: Added new template: {title}")
            except ValueError as e:
                # Template already exists (race condition)
                logger.debug(f"Job {self.job_id}: Template {title} already exists: {e}")
                # no need to count this as failed
                continue
            except Exception as e:
                logger.exception(f"Job {self.job_id}: Failed to add template {title}")
                tmp_info.error = str(e)

                self.result["pages_failed"].append(tmp_info.to_dict())

    def process(self) -> Dict[str, Any]:
        """Execute the collection processing logic."""

        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result["status"] = "failed"
            self.result["failed_at"] = datetime.now().isoformat()
            return self.result

        # Step 1: Fetch new templates from category and add them
        self._fetch_and_add_new_templates()

        if self.is_cancelled():
            logger.info(f"Job {self.job_id}: Cancelled after adding templates.")
            return self.result

        # Step 2: Get all templates (including newly added)
        templates = list_templates()
        self.result["summary"]["total"] = len(templates)

        if self.update_all:
            tmps_to_process = templates
            logger.info(f"Job {self.job_id}: Update all mode - processing all {len(tmps_to_process)} templates")
        else:
            tmps_to_process = [t for t in templates if not (t.main_file and t.last_world_file and t.source)]
            logger.info(f"Job {self.job_id}: Found {len(templates)} templates, {len(tmps_to_process)} need processing")

        per_item = self.get_priority(len(tmps_to_process))

        for n, template in enumerate(tmps_to_process, start=1):
            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self._save_progress()

            self.result["summary"]["processed"] += 1
            logger.info(f"Job {self.job_id}: Processing template {n}/{len(tmps_to_process)}: {template.title}")
            template_info = TemplateInfo(
                id=template.id,
                title=template.title,
                new_main_file="",
                last_world_file="",
                source="",
                status="",
            )
            logger.info(f"Job {self.job_id}: Fetching wikitext for {template.title}")
            # Fetch wikitext from Commons
            wikitext = get_page_text(template.title, site=self.site)

            if not wikitext:
                template_info.status = "failed"
                template_info.error = "Could not fetch wikitext from Commons"
                self.result["pages_failed"].append(template_info.to_dict())
                self.result["summary"]["failed"] += 1
                logger.warning(f"Job {self.job_id}: Could not fetch wikitext for {template.title}")
                continue

            template_data = {}
            skip_msg = "No changes needed"
            try:
                # Extract main file using find_main_title
                main_file = find_main_title(wikitext)
            except Exception as e:
                logger.error(f"Job {self.job_id}: Error while extracting main file: {e}")
                main_file = None

            if main_file and main_file != template.main_file:
                template_info.new_main_file = main_file
                template_data["main_file"] = main_file

            try:
                last_world_file = find_last_world_file_from_owidslidersrcs(wikitext)
            except Exception as e:
                logger.error(f"Job {self.job_id}: Error while extracting last world file: {e}")
                last_world_file = None

            if last_world_file and last_world_file != template.last_world_file:
                template_data["last_world_file"] = last_world_file
                template_info.last_world_file = last_world_file

            source = find_template_source(wikitext, check_grapher=False)
            if source and source != template.source:
                template_info.source = source
                template_data["source"] = source
                if "/grapher/" in source:
                    slug = source.split("/grapher/", maxsplit=1)[1].split("?")[0]
                    template_data["slug"] = slug or None
                else:
                    skip_msg = "source url does not have /grapher/"

            if not template.slug and not template_data.get("slug"):
                _slug = slugify_title(template.title)
                if _slug:
                    template_data["slug"] = _slug

            if not main_file and not last_world_file and not source:
                template_info.status = "failed"
                template_info.error = "Could not find (main file or last world file or source) in wikitext"
                self.result["pages_failed"].append(template_info.to_dict())
                self.result["summary"]["failed"] += 1
                logger.warning(
                    f"Job {self.job_id}: Could not find main file or last world file or source for {template.title}"
                )
                continue

            if not template_data:
                template_info.status = "skipped"
                template_info.error = skip_msg
                self.result["pages_skipped"].append(template_info.to_dict())
                logger.info(f"Job {self.job_id}: No changes for {template.title}")
                continue

            # Update template with main file
            logger.info(
                f"Job {self.job_id}: Updating {template.title} with main_file: {main_file} "
                f"and last_world_file: {last_world_file} "
                f"and source: {source}"
            )

            try:
                update_template_data(
                    template.id,
                    template_data,
                )

                template_info.status = "updated"
                self.result["pages_updated"].append(template_info.to_dict())

            except Exception as e:
                template_info.status = "failed"
                template_info.error = f"Exception: {str(e)}"
                template_info.error_type = type(e).__name__

                self.result["pages_failed"].append(template_info.to_dict())
                self.result["summary"]["failed"] += 1

                logger.exception(f"Job {self.job_id}: Error processing template {template.title}")

            if template_info.status == "updated" and self.check_cancel_db_periodic():
                logger.info(f"Job {self.job_id}: Cancelled due to periodic check")
                break

        # Update summary skipped count
        self.result["summary"]["skipped"] = len(self.result["pages_skipped"])

        logger.info(
            f"Job {self.job_id} completed: {len(self.result["pages_updated"])} updated, "
            f"{self.result['summary']['failed']} failed, "
            f"{self.result['summary']['skipped']} skipped"
        )

        return self.result


def collect_templates_data_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """
    Background worker to collect templates data.

    By default only processes templates missing data. Pass args={"update_all": "true"}
    to re-fetch and update ALL templates.

    Args:
        job_id: The job ID
        user: User authentication data
        cancel_event: Threading event for cancellation
        args: Optional arguments dict. Supports:
            - update_all: "true" to update all templates, not just those missing data.
    """

    logger.info(f"Starting job {job_id}: collect templates data")
    worker = CollectMainFilesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "collect_templates_data_entry",
    "CollectMainFilesWorker",
]
