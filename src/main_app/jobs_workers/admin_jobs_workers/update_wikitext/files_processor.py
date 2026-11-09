"""
Worker module for update_wikitext.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage
from ....api_services.files_service import FilesService
from ....data import get_slug_categories
from ....utils.wikitext import merge_categories, sort_categories
from ....utils.wikitext.cropped_file_text.other_versions import (
    OtherVersionsUpdater,
)
from .objects import OneStep, ProcessingFileInfo

logger = logging.getLogger(__name__)


class UpdateWikiTextProcessor:
    """
    process_one_item Steps:
        1. Check if file exists or skip it
        2. load file wikitext
        3. update text:
            a. Update author value `| Author=` in `Information` template using update_information_author()
                if author_citation or skip this step
            b.
                - load file languages using self.files_service.get_file_languages(file_name)
                - update `Svg lang` template to include all file languages using self.other_versions_updater.add_svg_langs(text, langs)
    """

    def __init__(self, site: Site) -> None:
        self.files_service = FilesService()
        self.site = site
        self.other_versions_updater = OtherVersionsUpdater()

        self.author_citation = ""

    def process_one_item(self, file_info: ProcessingFileInfo) -> bool:

        page = MwClientPage(file_info.title, self.site)
        # ----------------------------------
        # Step 1 - Check if file exists
        if not page.exists():
            file_info.status = "failed"
            file_info.error = "File does not exist"
            return False

        # ----------------------------------
        # Step 2 - load file wikitext
        if not self._step_load_template_text(page, file_info):
            return False

        # ----------------------------------
        # Step 3 - create_new_text
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

    def _step_load_template_text(self, page: MwClientPage, info: ProcessingFileInfo) -> bool:
        """Download the original Template wikitext. Returns True on success."""
        text = page.get_text()
        if not text:
            self._fail(info, info.steps.load_template_text, f"Could not retrieve text for {info.title}")
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
            f"Updating OWID page from [[{info.title}]]",
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
            summary=f"Creating OWID page from [[{info.title}]]",
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
        if info.title.startswith("Template:OWID/"):
            return info.title.replace("Template:OWID/", "OWID/", 1)

        return "OWID/" + info.title.removeprefix("Template:")

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


__all__ = [
    "UpdateWikiTextProcessor",
]
