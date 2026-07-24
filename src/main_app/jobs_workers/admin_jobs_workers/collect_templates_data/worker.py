"""
Worker module for collecting main files for templates.

"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Any

from mwclient.client import Site

from ....api_services import MwClientPage, fetch_grapher_metadata, get_category_members
from ....db.models import TemplateRecord
from ....db.services import (
    TemplateService,
    OwidChartsService,
    list_templates_need_update,
)
from ....db.templates_utils import extract_slug
from ....utils.wikitext import (
    find_main_title,
    find_newest_world_file,
    find_newest_year,
    find_template_source,
)
from ...base_worker import BaseObjectsJobWorker
from ..slugs_helpers import check_slugs
from .objects import CollectTemplatesDataWorkerObject, TemplateInfo

logger = logging.getLogger(__name__)


@dataclass
class TemplateData:
    id: int = 0
    title: str = ""
    main_file: str | None = None
    last_world_file: str | None = None
    last_world_year: int | None = None
    slug: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        if self.main_file:
            self.main_file = self.main_file.removeprefix("File:")
        if self.last_world_file:
            self.last_world_file = self.last_world_file.removeprefix("File:")


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
        return slug
    return None


class CollectMainFilesWorker(BaseObjectsJobWorker):
    """Worker for collecting main files for templates."""

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.site: Site | None = None

        super().__init__(job_id, user, cancel_event)
        self.result: CollectTemplatesDataWorkerObject = CollectTemplatesDataWorkerObject()

        self.args = args or {}
        self.template_service = TemplateService()
        self.owid_charts_service = OwidChartsService()
        self.result.args = self.args
        self.update_all = str(self.args.get("update_all", "")).lower() == "true"

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "collect_templates_data"

    # ------------------------------------------------------------------
    # pre process step
    # ------------------------------------------------------------------
    def _fetch_and_add_new_templates(self) -> None:
        """
        Fetch templates from the category and add new ones to the database.

        Returns:
            Number of new templates added
        """
        logger.info(f"Job {self.job_id}: Fetching templates from category")

        templates: list[TemplateRecord] = self.template_service.list_templates()
        existing_titles = {t.title for t in templates}

        # Get templates from category
        category_templates = self._get_category_members()

        logger.info(f"Job {self.job_id}: Found {len(category_templates)} templates in category")

        if not category_templates:
            return

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
                newest_year=None,
                source="",
                status="",
            )
            try:
                self.template_service.add_template_data({"title": title})
                self.result.pages_added.append(tmp_info.to_dict())
                logger.info(f"Job {self.job_id}: Added new template: {title}")
            except ValueError as e:
                # Template already exists (race condition)
                logger.debug(f"Job {self.job_id}: Template {title} already exists: {e}")
                # no need to count this as failed
                continue
            except Exception as e:
                logger.exception(f"Job {self.job_id}: Failed to add template {title}")
                tmp_info.error = str(e)

                self.result.pages_failed.append(tmp_info.to_dict())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_category_members(self) -> list:
        category = "Category:Pages using gadget owidslider"
        result = get_category_members(
            site=self.site,
            category_title=category,
            namespace=10,
        )

        logger.info(f"Found {len(result)} pages in category {category}")

        EXCLUDED_TEMPLATES = {"template:owidslider", "template:owid"}
        category_templates = [x for x in result if x.startswith("Template:") and x.lower() not in EXCLUDED_TEMPLATES]
        return category_templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------

    def _load_temp_info(self, template: TemplateData) -> TemplateInfo:
        template_info = TemplateInfo(
            id=template.id,
            title=template.title,
            new_main_file="",
            last_world_file="",
            newest_year=None,
            source="",
            status="",
        )
        if template.main_file:
            template_info.steps.main_file.value = template.main_file

        if template.last_world_file:
            template_info.steps.last_world_file.value = template.last_world_file

        template_info.steps.source.value = template.source
        template_info.steps.slug.value = template.slug

        return template_info

    def _process_one_item(self, template: TemplateData) -> bool:
        self.result.summary.processed += 1

        template_info = self._load_temp_info(template)

        logger.info(f"Job {self.job_id}: Fetching wikitext for {template.title}")
        # Fetch wikitext from Commons
        wikitext = MwClientPage(template.title, self.site).get_text()

        if not wikitext:
            template_info.status = "failed"
            template_info.error = "Could not fetch wikitext from Commons"
            self.result.pages_failed.append(template_info.to_dict())
            self.result.summary.failed += 1
            logger.warning(f"Job {self.job_id}: Could not fetch wikitext for {template.title}")
            return False

        template_data: dict[str, Any] = {
            "main_file": None,
            "last_world_file": None,
            "last_world_year": None,
            "slug": None,
            "source": None,
        }
        skip_msg = "No changes"

        # ------------------
        # template_info step # 1 main_file
        try:
            # Extract main file using find_main_title
            main_file = find_main_title(wikitext, remove_prefix=True)
            if not main_file:
                raise Exception("Could not find main file")
        except Exception as e:
            logger.error(f"Job {self.job_id}: Error while extracting main file: {e}")
            main_file = None
            template_info.steps.main_file._update(result="failed", msg=str(e))

        if main_file:
            if main_file != template.main_file:
                # template_info.new_main_file = main_file
                template_info.steps.main_file._update(result="updated", new_value=main_file)
                template_data["main_file"] = main_file
            else:
                template_info.steps.main_file._update(result="skipped", msg="No changes")

        # ------------------
        # template_info step # 2 last_world_file
        try:
            last_file = find_newest_world_file(wikitext, remove_prefix=True)
            if not last_file:
                raise Exception("Could not find newest world file")
        except Exception as e:
            logger.error(f"Job {self.job_id}: Error while extracting newest world file: {e}")
            last_file = None
            template_info.steps.last_world_file._update(result="failed", msg=str(e))

        if last_file:
            if last_file != template.last_world_file:
                # template_info.last_world_file = last_world_file
                template_info.steps.last_world_file._update(result="updated", new_value=last_file)
                template_data["last_world_file"] = last_file
            else:
                template_info.steps.last_world_file._update(result="skipped", msg="No changes")

        # ------------------
        # template_info step # 2 newest_year
        try:
            newest_year = find_newest_year(wikitext)
            if not newest_year:
                raise Exception("Could not find newest year")
        except Exception as e:
            logger.error(f"Job {self.job_id}: Error while extracting newest year: {e}")
            newest_year = None
            template_info.steps.newest_year._update(result="failed", msg=str(e))
        if newest_year:
            if newest_year != template.last_world_year:
                # template_info.newest_year = newest_year
                template_info.steps.newest_year._update(result="updated", new_value=newest_year)
                template_data["last_world_year"] = newest_year
            else:
                template_info.steps.newest_year._update(result="skipped", msg="No changes")

        # ------------------
        # template_info step # 4 source
        try:
            source = find_template_source(wikitext, check_grapher=False)
            if not source:
                raise Exception("Could not find source")
        except Exception as e:
            logger.error(f"Job {self.job_id}: Error while extracting source: {e}")
            source = None
            template_info.steps.source._update(result="failed", msg=str(e))

        if source:
            if source != template.source:
                # template_info.source = source
                template_info.steps.source._update(result="updated", new_value=source)
                template_data["source"] = source
            else:
                template_info.steps.source._update(result="skipped", msg="No changes")

        # ------------------
        # template_info step # 5 slug
        try:
            _slug = self._load_slug(template.title, template.slug, template_data.get("source", ""))
            if not _slug:
                raise Exception("Could not find slug")
        except Exception as e:
            logger.error(f"Job {self.job_id}: Error while extracting slug: {e}")
            _slug = None
            template_info.steps.slug._update(result="failed", msg=str(e))

        if _slug:
            if _slug != template.slug:
                template_info.steps.slug._update(result="updated", new_value=_slug)
                template_data["slug"] = _slug
            else:
                template_info.steps.slug._update(result="skipped", msg="No changes")

        # ------------------
        # update status
        if not main_file and not last_file and not newest_year and not source:
            template_info.status = "failed"
            template_info.error = "Could not find (main file or newest world file or source) in wikitext"
            self.result.pages_failed.append(template_info.to_dict())
            self.result.summary.failed += 1
            logger.warning(
                f"Job {self.job_id}: Could not find main file or newest world file or source for {template.title}"
            )
            return False

        template_data = {x: v for x, v in template_data.items() if v and v is not None}
        if not template_data:
            template_info.status = "skipped"
            template_info.error = skip_msg
            self.result.pages_skipped.append(template_info.to_dict())
            logger.info(f"Job {self.job_id}: No changes for {template.title}")
            return False

        # Update template with main file
        logger.info(
            f"Job {self.job_id}: Updating {template.title} with main_file: {main_file} "
            f"and last_world_file: {last_file} "
            f"and source: {source}"
        )

        try:
            self.template_service.update_template_data(
                template.id,
                template_data,
            )

            template_info.status = "updated"
            self.result.pages_updated.append(template_info.to_dict())
            return True

        except Exception as e:
            template_info.status = "failed"
            template_info.error = f"Exception: {str(e)}"
            template_info.error_type = type(e).__name__

            self.result.pages_failed.append(template_info.to_dict())
            self.result.summary.failed += 1

            logger.exception(f"Job {self.job_id}: Error processing template {template.title}")

        return False

    def slugify_title(self, template_title: str) -> str | None:
        slug = slugify_title(template_title)
        # Only assign slug if it exists in the owid_charts table
        if slug:
            try:
                self.owid_charts_service.get_chart_by_slug(slug)
                return slug
            except (LookupError, RuntimeError):
                return None

    def _load_slug(self, template_title: str, template_slug: str, template_source: str) -> str | None:
        _slug = extract_slug(template_source)

        if not _slug:
            _slug = self.slugify_title(template_title)

        _slug_to_check = _slug or template_slug

        if _slug_to_check:
            # Find slug redirect
            metadata = fetch_grapher_metadata(_slug_to_check)
            if metadata:
                check_slugs(_slug_to_check, metadata)

        if not _slug and "/grapher/" not in template_source:
            raise Exception("source url does not have /grapher/")

        return _slug

    def finish(self) -> None:
        # Update summary skipped count
        self.result.summary.skipped = len(self.result.pages_skipped)

        logger.info(
            f"Job {self.job_id} completed: {len(self.result.pages_updated)} updated, "
            f"{self.result.summary.failed} failed, "
            f"{self.result.summary.skipped} skipped"
        )

    # ------------------------------------------------------------------
    # sub public entry-point
    # ------------------------------------------------------------------

    def process_one(self, template_title: str) -> CollectTemplatesDataWorkerObject:
        """Process a single template by title."""

        template: TemplateRecord = self.template_service.get_template_by_title(template_title)
        if not template:
            logger.error(f"Job {self.job_id}: Template '{template_title}' not found")
            self.result.summary.total = 0
            self.result.status = "failed"
            self.log_errors(f"Template '{template_title}' not found")
            self.finish()
            return self.result

        self.result.summary.total = 1

        self._save_progress()

        logger.info(f"Job {self.job_id}: Processing single template {template.title}")

        _updated = self._process_one_item(template)
        if _updated:
            logger.info(f"Job {self.job_id}: Template {template.title} updated")

        self.finish()

        return self.result

    def process_all(self) -> CollectTemplatesDataWorkerObject:
        """Execute the collection processing logic."""
        # Step 1: Fetch new templates from category and add them
        self._fetch_and_add_new_templates()

        if self.is_cancelled():
            logger.info(f"Job {self.job_id}: Cancelled after adding templates.")
            return self.result

        # Step 2: Re-fetch all templates (including newly added)
        templates: list[TemplateRecord] = self.template_service.list_templates()
        self.result.summary.total = len(templates)

        if self.update_all:
            tmps_to_process = templates
            logger.info(f"Job {self.job_id}: Update all mode - processing all {len(tmps_to_process)} templates")
        else:
            tmps_to_process = [t for t in templates if not (t.main_file and t.last_world_file and t.source)]
            logger.info(f"Job {self.job_id}: Found {len(templates)} templates, {len(tmps_to_process)} need processing")

        return self.start_process(tmps_to_process)

    def start_process(self, tmps_to_process: list[TemplateRecord]) -> CollectTemplatesDataWorkerObject:

        # change TemplateRecord to TemplateData
        # templates_data = [TemplateData(**x.to_dict()) for x in tmps_to_process]
        templates_data = [
            TemplateData(
                id=x.id,
                title=x.title,
                main_file=x.main_file,
                last_world_file=x.last_world_file,
                last_world_year=x.last_world_year,
                slug=x.slug,
                source=x.source,
            )
            for x in tmps_to_process
        ]

        # Sort templates by priority
        per_item = self.get_priority(len(templates_data))

        for n, template in enumerate(templates_data, start=1):
            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self._save_progress()

            logger.info(f"Job {self.job_id}: Processing template {n}/{len(templates_data)}: {template.title}")

            _updated = self._process_one_item(template)

            if _updated and self.check_cancel_db_periodic():
                logger.info(f"Job {self.job_id}: Cancelled due to periodic check")
                break
        self.finish()

        return self.result

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> CollectTemplatesDataWorkerObject:
        """Execute the collection processing logic."""
        if not self._check_site():
            return self.result

        # Single template mode: if a title arg is provided, process only that one
        if self.args.get("title"):
            return self.process_one(self.args["title"])

        if self.args.get("list_titles") == "list_templates_need_update":
            templates_to_update = list_templates_need_update()
            templates_to_update_titles = {x.template_title for x in templates_to_update}

            templates: list[TemplateRecord] = self.template_service.list_templates()
            tmps_to_process = [x for x in templates if x.title in templates_to_update_titles]
            self.result.summary.total = len(tmps_to_process)
            return self.start_process(tmps_to_process)

        # Default mode: process all templates
        return self.process_all()


__all__ = [
    "CollectMainFilesWorker",
]
