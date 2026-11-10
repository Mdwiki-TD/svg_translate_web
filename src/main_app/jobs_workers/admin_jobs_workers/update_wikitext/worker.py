"""
Worker module for update_wikitext.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....database.services import ChartsAndTemplatesService, TemplateService
from ....utils.wikitext.legacy import get_titles
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from ...public_jobs_workers.copy_svg_langs.steps import extract_text_step
from .files_processor import UpdateWikiTextProcessor
from .objects import ProcessingFileInfo, UpdateFilesWikiTextObject

logger = logging.getLogger(__name__)


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
        self.files_processor = UpdateWikiTextProcessor(self.site)
        self.template_service = TemplateService()
        self.charts_and_tmps_service = ChartsAndTemplatesService()

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

    def process_titles(self, titles: list[str]) -> None:
        per_item = self.get_priority(len(titles))

        for n, file in enumerate(titles, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, len(titles), file)

            file_info = ProcessingFileInfo(title=file)

            ok = self.files_processor.process_one_item(file_info)
            self.result.update_status(file_info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        return self.result

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

        # ----------------------------------------------
        # Stage 3: Get template and template author_citation
        template = self.template_service.get_template_by_title(self.title)

        self.files_processor.author_citation = self.charts_and_tmps_service.get_author_citation(template) or ""
        # ----------------------------------------------
        # Stage 4: Extract Titles
        self.process_titles(self.titles)

        return self.result


__all__ = [
    "UpdateFilesWikiTextWorker",
]
