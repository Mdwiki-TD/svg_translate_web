"""
Worker module for add_lang_categories_to_owid_pages.

Iterates all ``OWID/*`` pages (main namespace, non-redirects) on Wikimedia
Commons, determines which languages the underlying SVG supports, and appends
``[[Category:<Lang>-language SVG]]`` entries to each page.

Authentication uses the current user's OAuth-bound Site (no env credentials).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from mwclient.client import Site

from ....api_services import MwClientPage
from ....api_services.files_service.file_langs import get_file_languages
from ....utils.wikitext.categories_utils import get_missing_categories_list
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from .objects import AddLangCategoriesWorkerObject, OneStep, PageInfo
from .utils import (
    build_category_names,
    extract_svg_file_name,
)

logger = logging.getLogger(__name__)


class AddLangCategoriesWorker(BaseObjectsJobWorker):
    """Background worker that adds language categories to OWID pages.

    Steps per page:
        1. Load page wikitext
        2. Extract SVG file name from Translate link
        3. Get languages from Commons file metadata API
        4. Build category lines from language codes
        5. Check which categories already exist on the page
        6. Save page with new categories appended
    """

    def __init__(self, data: JobsRunner) -> None:
        self.site: Site | None = None

        super().__init__(data)
        self.args = data.args or {}

        self.result: AddLangCategoriesWorkerObject = AddLangCategoriesWorkerObject(
            job_id=self.job_id,
            args=self.args,
        )

        self.limit_items = self.args.get("limit_items") or 0

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "add_lang_categories_to_owid_pages"

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> AddLangCategoriesWorkerObject:
        if not self._check_site():
            return self.result

        pages = self._collect_pages()
        self.result.summary.total = len(pages)
        self._save_progress()

        logger.info("Job %s: Found %d OWID page(s)", self.job_id, len(pages))

        per_item = self.get_priority(len(pages)) if pages else 1

        for n, page_title in enumerate(pages, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, len(pages), page_title)
            info = PageInfo(page_title=page_title)

            ok = self._process_one_item(info)
            self.update_status(info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        return self.result

    # ------------------------------------------------------------------
    # Page discovery
    # ------------------------------------------------------------------

    def _collect_pages(self) -> list[str]:
        """Collect OWID page titles from the main namespace."""
        titles: list[str] = []
        for page in self._iter_owid_pages():
            titles.append(page.name)

        if self.limit_items and isinstance(self.limit_items, int) and self.limit_items > 0:
            logger.info("Job %s: Limiting from %d to %d pages", self.job_id, len(titles), self.limit_items)
            titles = titles[: self.limit_items]

        return titles

    def _iter_owid_pages(self) -> Iterable:
        """Yield non-redirect pages with prefix ``OWID/`` in main namespace."""
        if self.site:
            return self.site.allpages(
                prefix="OWID/",
                namespace=0,
                filterredir="nonredirects",
            )
        return []

    # ------------------------------------------------------------------
    # Per-page orchestration
    # ------------------------------------------------------------------

    def _process_one_item(self, info: PageInfo) -> bool:

        page = MwClientPage(info.page_title, self.site)

        # Step 1 — load_page_text
        if not self._step_load_page_text(info, page):
            return False

        # Step 2 — extract_file_name
        if not self._step_extract_file_name(info):
            return False

        # Step 3 — get_languages
        if not self._step_get_languages(info):
            return False

        # Step 4 — build_categories
        if not self._step_build_categories(info):
            return False

        # Step 5 — check_existing
        new_categories = self._step_check_existing(info)
        if not new_categories:
            return False

        # Step 6 — save_page
        if not self._step_save_page(info, page, new_categories):
            return False

        info.status = "success"
        info.categories_added = new_categories
        return True

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_load_page_text(self, info: PageInfo, page: MwClientPage) -> bool:
        """Download the page wikitext. Returns True on success."""
        text = page.get_text()
        if not text:
            self._fail(info, info.steps.load_page_text, f"Could not retrieve text for {info.page_title}")
            return False

        info.steps.load_page_text = OneStep(result=True, msg="Loaded page text")
        info._text = text
        return True

    def _step_extract_file_name(self, info: PageInfo) -> bool:
        """Extract SVG file name from the Translate link. Returns True on success."""
        if not info._text:
            self._fail(info, info.steps.extract_file_name, f"No text found for {info.page_title}")
            return False

        file_name = extract_svg_file_name(info._text or "")
        if not file_name:
            self._fail(info, info.steps.extract_file_name, f"No Translate link found in {info.page_title}")
            self.result.summary.no_file += 1
            return False

        info.svg_file = file_name
        info.steps.extract_file_name = OneStep(result=True, msg=f"SVG file: {file_name}")
        return True

    def _step_get_languages(self, info: PageInfo) -> bool:
        """Call the Commons API to get available languages for the SVG file."""
        result = get_file_languages(info.svg_file or "")
        error = result.error
        langs = result.langs

        if error or not langs:
            self._fail(info, info.steps.get_languages, error or "No languages returned")
            return False

        if len(langs) == 1 and langs[0] == "en":
            info.steps.get_languages.msg = "Skipped — No non-English languages found"
            info.status = "skipped"
            return False

        info.lang_codes = langs
        info.steps.get_languages = OneStep(result=True, msg=f"Found {len(langs)} language(s): {', '.join(langs)}")
        return True

    def _step_build_categories(self, info: PageInfo) -> bool:
        """Build category names from language codes. Returns False if no valid codes."""
        categories = build_category_names(info.lang_codes)
        if not categories:
            self._fail(info, info.steps.build_categories, f"No recognised language codes in {info.lang_codes}")
            return False

        info.steps.build_categories = OneStep(
            result=True,
            msg=f"Built {len(categories)} candidate category name(s)",
        )
        # Store bare category names temporarily in _categories for use in next step
        info._categories = categories
        return True

    def _step_check_existing(self, info: PageInfo) -> list[str]:
        """Merge candidate categories into page text, skipping those already present.

        Uses ``merge_categories_into_text`` which handles deduplication via
        case-insensitive comparison.  Falls back to manual append when the page

        Returns:
            List of ``[[Category:…]]`` strings that were actually added
            (empty list means nothing to do).
        """
        candidate_names = info._categories
        original_text = info._text or ""

        new_categories = get_missing_categories_list(candidate_names, original_text)
        if not new_categories:
            info.steps.check_existing.msg = "Skipped — all language categories already exist"
            info.status = "skipped"
            return []

        missing_categories_str = "\n".join(new_categories)

        # Append the missing categories to the end of the new text
        merged_text = f"{original_text}\n{missing_categories_str}"

        info._text = merged_text
        info.steps.check_existing = OneStep(
            result=True,
            msg=f"{len(new_categories)} new category line(s) to add",
        )
        return new_categories

    def _step_save_page(self, info: PageInfo, page: MwClientPage, new_categories: list[str]) -> bool:
        """Save the page with the already-merged text. Returns True on success."""
        cat_summary = ", ".join(new_categories)

        text = info._text
        if not text:
            self._fail(info, info.steps.save_page, f"No text to save for {info.page_title}")
            return False

        res = page.edit(
            text,
            summary=f"Adding language categories: {cat_summary}",
        )

        if res.get("success"):
            info.steps.save_page = OneStep(
                result=True,
                msg=f"Saved {info.page_title}",
                newrevid=res.get("newrevid", 0),
            )
            self.result.summary.success += 1
            return True

        err = res.get("error", "Unknown error")
        self._fail(info, info.steps.save_page, err)
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fail(self, info: PageInfo, step_obj: OneStep, error: str) -> None:
        """Mark a step and the info as failed."""
        step_obj.result = False
        step_obj.msg = error
        info.status = "failed"
        info.error = error

    def update_status(self, info: PageInfo):
        self.result.summary.processed += 1

        if info.status in ["pending", "running"]:
            info.status = "completed"

        if info.status == "skipped":
            self.result.pages_skipped.append(info)

        elif info.status == "success":
            self.result.pages_success.append(info)

        elif info.status == "failed":
            self.result.pages_failed.append(info)
            self.result.summary.failed += 1

        else:
            self.result.pages_processed.append(info)


__all__ = [
    "AddLangCategoriesWorker",
]
