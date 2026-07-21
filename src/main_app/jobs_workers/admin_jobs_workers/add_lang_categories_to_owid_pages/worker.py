"""
Worker module for add_lang_categories_to_owid_pages.

Iterates all ``OWID/*`` pages (main namespace, non-redirects) on Wikimedia
Commons, determines which languages the underlying SVG supports, and appends
``[[Category:<Lang>-language SVG]]`` entries to each page.

Authentication uses the current user's OAuth-bound Site (no env credentials).
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from mwclient.client import Site

from ....api_services import MwClientPage
from ....utils.file_langs import get_file_languages
from ....utils.wikitext.categories_utils import get_missing_categories_list
from ...base_worker import BaseObjectsJobWorker
from .objects import AddLangCategoriesWorkerObject
from .utils import (
    build_category_names,
    extract_svg_file_name,
)

logger = logging.getLogger(__name__)

StepResult = dict[str, Any]


@dataclass
class PageInfo:
    """Holds all state for a single OWID page being processed."""

    page_title: str
    svg_file: str | None = None
    lang_codes: list[str] = field(default_factory=list)
    categories_added: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    error: str | None = None
    steps: dict[str, StepResult] = field(
        default_factory=lambda: {
            "load_page_text": {"result": None, "msg": ""},
            "extract_file_name": {"result": None, "msg": ""},
            "get_languages": {"result": None, "msg": ""},
            "build_categories": {"result": None, "msg": ""},
            "check_existing": {"result": None, "msg": ""},
            "save_page": {"result": None, "msg": ""},
        }
    )

    # Internal temporary state
    _text: str | None = None
    _categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_title": self.page_title,
            "svg_file": self.svg_file,
            "lang_codes": self.lang_codes,
            "categories_added": self.categories_added,
            "timestamp": self.timestamp,
            "status": self.status,
            "error": self.error,
            "steps": self.steps,
        }


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

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.site: Site | None = None

        super().__init__(job_id, user, cancel_event)
        self.result: AddLangCategoriesWorkerObject = AddLangCategoriesWorkerObject()

        self.args = args or {}
        self.result.args = self.args
        self.limit_items = self.args.get("limit_items") or 0

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "add_lang_categories_to_owid_pages"

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
            ok = self._process_one_item(page_title)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

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

    def _process_one_item(self, page_title: str) -> bool:
        self.result.summary.processed += 1

        info = PageInfo(page_title=page_title)
        page = MwClientPage(page_title, self.site)

        # Step 1 — load_page_text
        if not self._step_load_page_text(info, page):
            self.result.pages_failed.append(info.to_dict())
            return False

        # Step 2 — extract_file_name
        if not self._step_extract_file_name(info):
            self.result.pages_failed.append(info.to_dict())
            return False

        # Step 3 — get_languages
        if not self._step_get_languages(info):
            self.result.pages_failed.append(info.to_dict())
            return False

        # Step 4 — build_categories
        if not self._step_build_categories(info):
            self.result.pages_skipped.append(info.to_dict())
            return False

        # Step 5 — check_existing
        new_categories = self._step_check_existing(info)
        if not new_categories:
            self.result.pages_skipped.append(info.to_dict())
            return False

        # Step 6 — save_page
        if not self._step_save_page(info, page, new_categories):
            self.result.pages_failed.append(info.to_dict())
            return False

        info.status = "completed"
        info.categories_added = new_categories
        self.result.pages_success.append(info.to_dict())
        return True

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_load_page_text(self, info: PageInfo, page: MwClientPage) -> bool:
        """Download the page wikitext. Returns True on success."""
        text = page.get_text()
        if not text:
            self._fail(info, "load_page_text", f"Could not retrieve text for {info.page_title}")
            return False

        info.steps["load_page_text"] = {"result": True, "msg": "Loaded page text"}
        info._text = text
        return True

    def _step_extract_file_name(self, info: PageInfo) -> bool:
        """Extract SVG file name from the Translate link. Returns True on success."""
        if not info._text:
            self._fail(info, "extract_file_name", f"No text found for {info.page_title}")
            return False

        file_name = extract_svg_file_name(info._text or "")
        if not file_name:
            self._fail(info, "extract_file_name", f"No Translate link found in {info.page_title}")
            self.result.summary.no_file += 1
            return False

        info.svg_file = file_name
        info.steps["extract_file_name"] = {"result": True, "msg": f"SVG file: {file_name}"}
        return True

    def _step_get_languages(self, info: PageInfo) -> bool:
        """Call the Commons API to get available languages for the SVG file."""
        result = get_file_languages(info.svg_file or "")
        error = result.get("error")
        langs = result.get("langs")

        if error or not langs:
            self._fail(info, "get_languages", error or "No languages returned")
            return False

        info.lang_codes = langs
        info.steps["get_languages"] = {"result": True, "msg": f"Found {len(langs)} language(s): {', '.join(langs)}"}
        return True

    def _step_build_categories(self, info: PageInfo) -> bool:
        """Build category names from language codes. Returns False if no valid codes."""
        categories = build_category_names(info.lang_codes)
        if not categories:
            self._fail(info, "build_categories", f"No recognised language codes in {info.lang_codes}")
            return False

        info.steps["build_categories"] = {
            "result": True,
            "msg": f"Built {len(categories)} candidate category name(s)",
            "categories": categories,
        }
        # Store bare category names temporarily in _categories for use in next step
        info._categories = categories
        return True

    def _step_check_existing(self, info: PageInfo) -> list[str]:
        """Merge candidate categories into page text, skipping those already present.

        Uses ``merge_categories_into_text`` which handles deduplication via
        case-insensitive comparison.  Falls back to manual append when the page
        has no existing categories (known limitation of the merge function).

        Returns:
            List of ``[[Category:…]]`` strings that were actually added
            (empty list means nothing to do).
        """
        candidate_names = info._categories
        original_text = info._text

        new_categories = get_missing_categories_list(candidate_names, original_text)
        if not new_categories:
            info.steps["check_existing"] = {
                "result": None,
                "msg": "Skipped — all language categories already exist",
            }
            info.status = "skipped"
            return []

        missing_categories_str = "\n".join(new_categories)

        # Append the missing categories to the end of the new text
        merged_text = f"{original_text}\n{missing_categories_str}"

        info._text = merged_text
        info.steps["check_existing"] = {
            "result": True,
            "msg": f"{len(new_categories)} new category line(s) to add",
        }
        return new_categories

    def _step_save_page(self, info: PageInfo, page: MwClientPage, new_categories: list[str]) -> bool:
        """Save the page with the already-merged text. Returns True on success."""
        cat_summary = ", ".join(new_categories)

        text = info._text
        if not text:
            self._fail(info, "save_page", f"No text to save for {info.page_title}")
            return False

        res = page.edit(
            text,
            summary=f"Adding language categories: {cat_summary}",
        )

        if res.get("success"):
            info.steps["save_page"] = {
                "result": True,
                "msg": f"Saved {info.page_title}",
                "newrevid": res.get("newrevid", 0),
            }
            self.result.summary.success += 1
            return True

        err = res.get("error", "Unknown error")
        self._fail(info, "save_page", err)
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fail(self, info: PageInfo, step: str, error: str) -> None:
        """Mark a step and the page as failed, and increment the summary counter."""
        info.steps[step] = {"result": False, "msg": error}
        info.status = "failed"
        info.error = error
        self.result.summary.failed += 1


__all__ = [
    "AddLangCategoriesWorker",
]
