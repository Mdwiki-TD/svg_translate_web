"""
Worker module for update_wikitext.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services.files_service import FilesService

from ....api_services import MwClientPage
from ....data import get_slug_categories
from ....database.models import TemplateRecord
from ....database.services import TemplateService
from ....utils.wikitext import merge_categories, sort_categories
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from .objects import UpdateFilesWikiTextObject, OneStep, ProcessingFileInfo

from ....utils.wikitext import get_titles
from ...public_jobs_workers.copy_svg_langs.steps import extract_text_step
from ....utils.wikitext.cropped_file_text.other_versions import (
    OtherVersionsUpdater,
)

logger = logging.getLogger(__name__)


class UpdateWikiTextProcessor:
    """
    process_one_item Steps:
        1. Check if file exists or skip it
        2. load file wikitext
        3. Update author value `| Author=` in `Information` template using update_information_author()
            if author_citation or skip this step
        4.
            - load file languages using self.files_service.get_file_languages(file_name)
            - update `Svg lang` template to include all file languages using self.other_versions_updater.add_svg_langs(text, langs)
    """

    def __init__(self, files_service: FilesService, site: Site) -> None:
        self.files_service = files_service
        self.site = site
        self.author_citation = ""
        self.other_versions_updater = OtherVersionsUpdater()

    def process_one_item(self, file_info: ProcessingFileInfo) -> bool:
        # ----------------------------------
        # Step 1 - load_template_text
        if not self._step_load_template_text(file_info):
            return False

        # ----------------------------------
        # Step 2 - create_new_text
        if not self._step_create_new_text(file_info):
            return False

        if file_info.new_wikitext and file_info.slug:
            categories = get_slug_categories(file_info.slug)
            file_info.new_wikitext = self.add_slug_categories(file_info.new_wikitext, categories)

        # ----------------------------------
        # Step 2 A) - check if new page already exists
        new_title = self.create_new_page_title(file_info)

        page = MwClientPage(new_title, self.site)

        if page.exists():
            # ----------------------------------
            # Step 3 - compare if text need to be updated
            upd_step = self._step_update(file_info, new_title)

            return upd_step is True

        # Step 4 - create_new_page
        create_step = self._step_create_new_page(file_info)
        if create_step is False:
            return False

        elif create_step is True:
            return True

        # dead code?
        file_info.status = "completed"
        return True

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_load_template_text(self, info: ProcessingFileInfo) -> bool:
        """Download the original Template wikitext. Returns True on success."""
        text = MwClientPage(info.template_title, self.site).get_text()
        if not text:
            self._fail(info, info.steps.load_template_text, f"Could not retrieve text for {info.template_title}")
            return False

        info.steps.load_template_text = OneStep(result=True, msg="Loaded template text")
        info.wikitext = text
        return True

    def _step_create_new_text(self, info: ProcessingFileInfo) -> bool:
        """Generate the new OWID page wikitext. Returns True on success."""
        try:
            new_text = ""
            info.steps.create_new_text = OneStep(result=True, msg="Target wikitext generated")
            info.new_wikitext = new_text
            return True

        except Exception as exc:
            self._fail(info, info.steps.create_new_text, str(exc))
            return False

    def _step_update(self, info: ProcessingFileInfo, new_title: str) -> bool | None:
        """
        compare the target OWID page content.
        If identical, skip creation. If different, update here and return False.
        Returns True to continue to Step 4 (Creation) if page does not exist.
        """
        # Page exists, check if update is needed
        new_title_page = MwClientPage(new_title, self.site)

        current_text = new_title_page.get_text()
        if not current_text:
            self._fail(info, info.steps.update_text, f"Could not retrieve text for {new_title}")
            return False

        # extend categories from current text
        info.new_wikitext = merge_categories(current_text, info.new_wikitext)
        info.new_wikitext = sort_categories(info.new_wikitext)

        # sort current_text categories to compare with new text
        current_text = sort_categories(current_text)

        if current_text.strip() == info.new_wikitext.strip():
            info.steps.update_text.msg = "Skipped - page content is already identical"
            info.status = "skipped"
            info.new_page_title = new_title
            return None  # nothing to update

        # Content is different, perform update
        res = new_title_page.edit(
            info.new_wikitext,
            f"Updating OWID page from [[{info.template_title}]]",
        )

        if res["success"]:
            info.steps.update_text = OneStep(
                result=True,
                msg=f"Updated page: {new_title}",
                newrevid=res.get("newrevid", 0),
            )
            info.new_page_title = new_title
            info.status = "updated"
            return True

        err = res.get("error", "Unknown error")
        self._fail(info, info.steps.update_text, err)
        return False

    def _step_create_new_page(self, info: ProcessingFileInfo) -> bool:
        """Create/Update the OWID gallery page on Commons. Returns True on success."""
        # Expected pattern: Template:OWID/... -> OWID/...
        new_title = self.create_new_page_title(info)

        new_title_page = MwClientPage(new_title, self.site)

        res = new_title_page.create(
            info.new_wikitext,
            summary=f"Creating OWID page from [[{info.template_title}]]",
        )

        if not res["success"]:
            err = res.get("error", "Unknown error")
            self._fail(info, info.steps.create_new_page, err)
            return False

        info.steps.create_new_page = OneStep(
            result=True,
            msg=f"Created: {new_title}",
            newrevid=res.get("newrevid", 0),
        )
        info.new_page_title = new_title
        info.status = "created"
        return True

    def create_new_page_title(self, info: ProcessingFileInfo) -> str:
        if info.template_title.startswith("Template:OWID/"):
            return info.template_title.replace("Template:OWID/", "OWID/", 1)

        return "OWID/" + info.template_title.removeprefix("Template:")

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------
    def add_slug_categories(self, new_text: str, categories: list[str]) -> str:
        for x in categories:
            if x not in new_text:
                new_text += f"\n[[{x}]]"

        return new_text

    def _fail(self, info: ProcessingFileInfo, step_obj: OneStep, error: str) -> None:
        """Mark a step and the info as failed."""
        step_obj.result = False
        step_obj.msg = error
        info.status = "failed"
        info.error = error


class UpdateFilesWikiTextWorker(BaseObjectsJobWorker):
    """
    Worker for update_wikitext.
    Steps:
        1. extract_text: load template wikitext using extract_text_step()
        2. extract_titles: get all files names from wikitext into self.titles using get_titles(text)
        3. get template `author_citation` using `self.files_processor.author_citation = self._get_author_citation(template)`
        4. run process_titles with self.titles.
    """

    def __init__(self, data: JobsRunner) -> None:
        self.site: Site | None = None

        super().__init__(data)
        self.args = data.args or {}

        self.result: UpdateFilesWikiTextObject = UpdateFilesWikiTextObject(
            job_id=self.job_id,
            args=self.args,
        )

        self.title = self.args.get("template_name") or ""
        self.titles: list[str] = []
        self.files_service = FilesService()
        self.files_processor = UpdateWikiTextProcessor(self.files_service, self.site)

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "update_wikitext"

    def _extract_titles_step(self) -> bool:
        self.titles = get_titles(self.text)

        if not self.titles:
            self.result.status = "failed"
            return False

        return True

    def _extract_text_step(self) -> bool | None:
        # {"success": False | True, "text": "", "error": None | "error"}
        step_result = extract_text_step(
            self.title,
            self.site,
        )
        text = step_result.get("text", "")

        if step_result.get("success") and text:
            self.text = text
            return True

        self.result.status = "failed"
        return False

    def process(self) -> UpdateFilesWikiTextObject:
        """Execute the full pipeline."""
        if not self._check_site():
            return self.result

        # update site after calling _check_site
        if self.site is None:
            raise ValueError("Site is not set")

        if not self.title:
            logger.error("No title found")
            self.result.status = "failed"
            return self.result

        self.result.title = self.title

        # ----------------------------------------------
        # Stage 1: Extract Text
        self._save_progress()

        if not self._extract_text_step():
            return self.result

        # ----------------------------------------------
        # Stage 2: Extract Titles
        if not self._extract_titles_step():
            return self.result

        self.result.summary.total = len(self.titles)
        self._save_progress()

        logger.info("Job %s: Found %d File.", self.job_id, self.result.summary.total)

        self.process_titles(self.titles)

        return self.result

    def process_titles(self, titles: list[str]) -> None:
        per_item = self.get_priority(len(titles))

        for n, file in enumerate(titles, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, len(titles), file)

            file_info = ProcessingFileInfo(title=file)

            ok = self.files_processor.process_one_item(file_info)
            self.update_status(file_info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        return self.result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def update_status(self, info: ProcessingFileInfo) -> None:
        """ """
        self.result.summary.processed += 1

        if info.status in ["pending", "running"]:
            info.status = "completed"

        if info.status == "skipped":
            self.result.pages_skipped.append(info)

        elif info.status == "failed":
            self.result.pages_failed.append(info)

        elif info.status == "updated":
            self.result.pages_updated.append(info)

        elif info.status == "created":
            self.result.pages_created.append(info)

        else:
            self.result.pages_processed.append(info)


__all__ = [
    "UpdateFilesWikiTextWorker",
]
