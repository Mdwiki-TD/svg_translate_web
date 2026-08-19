"""
Worker module for collecting main files for templates.

"""

from __future__ import annotations

import logging
from typing import Any

from mwclient.client import Site

from ....api_services import MwClientPage, fetch_grapher_metadata_raw, get_category_members
from ....database.exceptions import DuplicateRecordError
from ....database.models import TemplateRecord
from ....database.services import (
    OwidChartsService,
    TemplateService,
    ViewsService,
)
from ....database.templates_utils import extract_slug
from ....utils.wikitext import (
    count_svg_files,
    find_main_title,
    find_newest_world_file,
    find_newest_year,
    find_template_source,
)
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from ..slugs_helpers import check_slugs
from .objects import (
    CollectStepResult,
    CollectTemplatesDataMapping,
    TemplateData,
    TemplateInfos,
)

logger = logging.getLogger(__name__)


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


class OneFileProcessor:

    def __init__(self, job_id: int, site: Site, template_service: TemplateService) -> None:
        self.job_id = job_id
        self.site = site
        self.template_service = template_service
        self.owid_charts_service = OwidChartsService()

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------

    def _process_one_item(self, template_info: TemplateInfos, template: TemplateData) -> bool:

        logger.info(f"Job {self.job_id}: Fetching wikitext for {template.title}")
        # Fetch wikitext from Commons
        wikitext = MwClientPage(template.title, self.site).get_text()

        if not wikitext:
            template_info.status = "failed"
            template_info.error = "Could not fetch wikitext from Commons"
            logger.warning(f"Job {self.job_id}: Could not fetch wikitext for {template.title}")
            return False

        db_data: dict[str, Any] = {
            "main_file": None,
            "last_world_file": None,
            "last_world_year": None,
            "slug": None,
            "source": None,
            "files": None,
        }

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
            template_info.steps.main_file._update_if_diff(new_value=main_file)

            if main_file != template.main_file:
                db_data["main_file"] = main_file

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
            template_info.steps.last_world_file._update_if_diff(new_value=last_file)

            if last_file != template.last_world_file:
                db_data["last_world_file"] = last_file

        # ------------------
        # template_info step # 2 newest_year
        try:
            newest_y = find_newest_year(wikitext)
            if not newest_y:
                raise Exception("Could not find newest year")
        except Exception as e:
            logger.error(f"Job {self.job_id}: Error while extracting newest year: {e}")
            newest_y = None
            template_info.steps.newest_year._update(result="failed", msg=str(e))

        if newest_y:
            template_info.steps.newest_year._update_if_diff(new_value=newest_y)

            if newest_y != template.last_world_year:
                db_data["last_world_year"] = newest_y

        # ------------------
        # template_info step # 4 source
        source_step: CollectStepResult = template_info.steps.source
        try:
            source = find_template_source(wikitext, check_grapher=False)
            if not source:
                raise Exception("Could not find source")
        except Exception as e:
            logger.error(f"Job {self.job_id}: Error while extracting source: {e}")
            source = None
            source_step._update(result="failed", msg=str(e))

        if source:
            source_step._update_if_diff(new_value=source)
            if source != template.source:
                db_data["source"] = source

        # ------------------
        # template_info step # 5 slug
        try:
            _slug = self._load_slug(template.title, template.slug, db_data.get("source"))
            if not _slug:
                raise Exception("Could not find slug")
        except Exception as e:
            logger.error(f"Job {self.job_id}: Error while extracting slug: {e}")
            _slug = None
            template_info.steps.slug._update(result="failed", msg=str(e))

        if _slug:
            template_info.steps.slug._update_if_diff(new_value=_slug)
            if _slug != template.slug:
                db_data["slug"] = _slug

        # ------------------
        files_len = count_svg_files(wikitext)
        if files_len:
            template_info.steps.files._update_if_diff(new_value=files_len)
            if files_len != template.files:
                db_data["files"] = files_len

        # ------------------
        # update status
        if not main_file and not last_file and not newest_y and not source and not files_len:
            template_info.status = "failed"
            template_info.error = "Could not find (main file or newest world file or source) in wikitext"
            logger.warning(
                f"Job {self.job_id}: Could not find main file or newest world file or source for {template.title}"
            )
            return False

        db_data = {x: v for x, v in db_data.items() if v and v is not None}
        if not db_data:
            template_info.status = "skipped"
            template_info.error = "No changes"
            logger.info(f"Job {self.job_id}: No changes for {template.title}")
            return False

        # Update template with main file
        logger.info(
            f"Job {self.job_id}: Updating {template.title} with main_file: {main_file} "
            f"and last world file: {last_file} "
            f"and source: {source}"
        )

        return self._update_db(template, db_data, template_info)

    def _update_db(
        self,
        template: TemplateData,
        data: dict[str, Any],
        template_info: TemplateInfos,
    ) -> bool:
        try:
            self.template_service.update_template_data(template.id, data)
            template_info.status = "updated"
            return True

        except Exception as e:
            template_info.status = "failed"
            template_info.error = f"Exception: {str(e)}"
            template_info.error_type = type(e).__name__

            logger.exception(f"Job {self.job_id}: Error processing template {template.title}")

        return False

    def _load_slug(self, template_title: str, template_slug: str, template_source: str | None) -> str | None:
        if template_source is None:
            template_source = ""

        _slug = extract_slug(template_source)

        if not _slug:
            _slug = self._slugify_title(template_title)

        _slug_to_check = _slug or template_slug

        if _slug_to_check:
            # Find slug redirect
            metadata = fetch_grapher_metadata_raw(_slug_to_check)
            if metadata and metadata.data:
                check_slugs(_slug_to_check, metadata.data)

        if not _slug and "/grapher/" not in template_source:
            raise Exception("source url does not have /grapher/")

        return _slug

    def _slugify_title(self, template_title: str) -> str | None:
        slug = slugify_title(template_title)
        # Only assign slug if it exists in the owid_charts table
        if slug:
            try:
                if self.owid_charts_service.get_chart_by_slug(slug):
                    return slug
                return None
            except (LookupError, RuntimeError):
                return None
        return None


class CollectMainFilesWorker(BaseObjectsJobWorker):
    """Worker for collecting main files for templates."""

    def __init__(self, data: JobsRunner) -> None:
        self.site: Site | None = None

        super().__init__(data)

        self.args = data.args or {}
        self.result: CollectTemplatesDataMapping = CollectTemplatesDataMapping(
            job_id=self.job_id,
            args=self.args,  # pyright: ignore[reportCallIssue]
        )

        self.template_service = TemplateService()
        self.views_service = ViewsService()

        self.update_all = str(self.args.get("update_all", "")).lower() == "true"
        self.files_processor = OneFileProcessor(self.job_id, self.site, self.template_service)

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

        templates: list[TemplateRecord] = self.template_service.list()
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

            tmp_info = TemplateInfos(
                id=n,
                title=title,
                source="",
                status="",
            )
            try:
                self.template_service.add_template_data({"title": title})
                self.result.pages_added.append(tmp_info)
                logger.info(f"Job {self.job_id}: Added new template: {title}")

            except (DuplicateRecordError, ValueError) as e:
                # Template already exists (race condition)
                logger.debug(f"Job {self.job_id}: Template {title} already exists: {e}")
                # no need to count this as failed
                continue

            except Exception as e:
                logger.exception(f"Job {self.job_id}: Failed to add template {title}")
                tmp_info.error = str(e)

                self.result.pages_failed.append(tmp_info)

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

        EXCLUDED_TEMPLATES = {"template:owid", "template:owidslider"}
        category_templates = [x for x in result if x.startswith("Template:") and x.lower() not in EXCLUDED_TEMPLATES]
        return category_templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------

    def _process_one_item(self, template: TemplateData) -> bool:
        self.result.summary.processed += 1

        template_info = TemplateInfos.from_template(template)

        ok = self.files_processor._process_one_item(template_info, template)

        if template_info.status.lower() in ["pending", "running"]:
            template_info.status = "completed"

        if template_info.status == "updated":
            self.result.pages_updated.append(template_info)

        elif template_info.status == "skipped":
            self.result.pages_skipped.append(template_info)

        elif template_info.status == "failed":
            self.result.pages_failed.append(template_info)
        else:
            self.result.pages_processed.append(template_info)

        return ok

    def finish(self) -> None:
        # Update summary skipped count
        self.result.summary.skipped = len(self.result.pages_skipped)
        self.result.summary.failed = len(self.result.pages_failed)

        logger.info(
            f"Job {self.job_id} completed: {len(self.result.pages_updated)} updated, "
            f"{self.result.summary.failed} failed, "
            f"{self.result.summary.skipped} skipped"
        )

    # ------------------------------------------------------------------
    # sub public entry-point
    # ------------------------------------------------------------------

    def process_one(self, template_title: str) -> CollectTemplatesDataMapping:
        """Process a single template by title."""

        template = self.template_service.get_template_by_title(template_title)
        if not template:
            logger.error(f"Job {self.job_id}: Template '{template_title}' not found")
            self.result.summary.total = 0
            self.result.status = "failed"
            self.log_errors(f"Template '{template_title}' not found")
            self.finish()
            return self.result

        self.result.summary.total = 1

        self._save_progress()

        logger.debug(f"Job {self.job_id}: Processing single template {template.title}")

        _updated = self._process_one_item(template)
        if _updated:
            logger.debug(f"Job {self.job_id}: Template {template.title} updated")

        self.finish()

        return self.result

    def process_all(self) -> CollectTemplatesDataMapping:
        """Execute the collection processing logic."""
        # Step 1: Fetch new templates from category and add them
        self._fetch_and_add_new_templates()

        if self.is_cancelled():
            logger.info(f"Job {self.job_id}: Cancelled after adding templates.")
            return self.result

        # Step 2: Re-fetch all templates (including newly added)
        templates: list[TemplateRecord] = self.template_service.list()
        self.result.summary.total = len(templates)

        if self.update_all:
            tmps_to_process = templates
            logger.info(f"Job {self.job_id}: Update all mode - processing all {len(tmps_to_process)} templates")
        else:
            tmps_to_process = [t for t in templates if not (t.main_file and t.last_world_file and t.source)]
            logger.info(f"Job {self.job_id}: Found {len(templates)} templates, {len(tmps_to_process)} need processing")

        return self.start_process(tmps_to_process)

    def start_process(self, tmps_to_process: list[TemplateRecord]) -> CollectTemplatesDataMapping:

        # change TemplateRecord to TemplateData
        templates_data = [TemplateData.from_template(x) for x in tmps_to_process]

        # Sort templates by priority
        per_item = self.get_priority(len(templates_data))

        for n, template in enumerate(templates_data, start=1):
            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self._save_progress()

            logger.debug(f"Job {self.job_id}: Processing template {n}/{len(templates_data)}: {template.title}")

            _updated = self._process_one_item(template)

            if _updated and self.check_cancel_db_periodic():
                logger.info(f"Job {self.job_id}: Cancelled due to periodic check")
                break
        self.finish()

        return self.result

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> CollectTemplatesDataMapping:
        """Execute the collection processing logic."""
        if not self._check_site():
            return self.result

        # update site after calling _check_site
        if self.site is None:
            raise ValueError("Site is not set")

        self.files_processor.site = self.site

        # Single template mode: if a title arg is provided, process only that one
        if self.args.get("title"):
            return self.process_one(self.args["title"])

        if self.args.get("list_titles") == "list_templates_need_update":
            templates_to_update = self.views_service.list_templates_need_update()
            templates_to_update_titles = {x.template_title for x in templates_to_update}

            templates: list[TemplateRecord] = self.template_service.list()
            tmps_to_process = [x for x in templates if x.title in templates_to_update_titles]
            self.result.summary.total = len(tmps_to_process)
            return self.start_process(tmps_to_process)

        # Default mode: process all templates
        return self.process_all()


__all__ = [
    "CollectMainFilesWorker",
]
