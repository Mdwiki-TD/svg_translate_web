"""
Worker module for update_wikitext.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage
from ....api_services.files_service import FilesService
from ....utils.new_wikitext import InformationAuthorUpdater
from ....utils.new_wikitext.other_versions import OtherVersionsUpdater
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
        text = page.get_text()
        if not text:
            self._fail(file_info, file_info.steps.load_text, f"Could not retrieve text for {file_info.title}")
            return False

        file_info.steps.load_text = OneStep(result=True, msg="Loaded template text")

        # ----------------------------------
        # Step 3 - update text
        file_langs = self.files_service.get_file_languages(file_info.title)
        if file_langs.langs:
            if "en" in file_langs.langs:
                file_langs.langs.remove("en")

            logger.info("File %s has languages: %r", file_info.title, file_langs.langs)
            file_info.langs = file_langs.langs or []

        new_wikitext = self._step_update_author(text, file_info)
        new_wikitext = self._step_update_langs(new_wikitext, file_info)

        if new_wikitext.strip() == text.strip():
            file_info.status = "skipped"
            # file_info.error = "No changes to save"
            return False

        # ----------------------------------
        # Step 3 - save new text
        if not self._step_save_text(new_wikitext, page, file_info):
            return False

        file_info.status = "completed"
        return True

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_update_author(self, text: str, info: ProcessingFileInfo) -> bool:
        """ """
        if not self.author_citation:
            info.steps.update_author.result = None
            info.steps.update_author.msg = "Skipped - no author citation provided"
            return text

        new_wikitext = InformationAuthorUpdater.update_information_author(
            text=text,
            author_citation=self.author_citation,
        )
        if text.strip() != new_wikitext.strip() and self.author_citation in new_wikitext:
            info.steps.update_author.result = True
            info.steps.update_author.msg = f"Author saved: {self.author_citation}"

        return new_wikitext

    def _step_update_langs(self, text: str, info: ProcessingFileInfo) -> str:
        """ """
        new_wikitext = self.other_versions_updater.add_svg_langs(
            text,
            info.langs,
            sort=False,
            delete_values=["en"],
        )

        if text.strip() == new_wikitext.strip():
            info.steps.update_langs.msg = "Skipped - page content is already identical"
            return text  # nothing to update

        info.steps.update_langs.result = True
        info.steps.update_langs.msg = f"Updated page: {info.title}"
        return new_wikitext

    def _step_save_text(self, new_wikitext: str, page: MwClientPage, info: ProcessingFileInfo) -> bool:
        """ """
        summary = info.create_summary_message(self.author_citation)

        if not summary:
            self._fail(info, info.steps.save_page, "No changes to save")
            return False

        res = page.edit(
            new_wikitext,
            summary=summary,
        )

        if res["success"]:
            info.steps.save_page = OneStep(
                result=True,
                msg=f"Updated page: {info.title}",
                newrevid=res.get("newrevid", 0),
            )
            info.status = "updated"
            return True

        err = res.get("error", "Unknown error")
        self._fail(info, info.steps.save_page, err)
        return False

    def _fail(self, info: ProcessingFileInfo, step_obj: OneStep, error: str) -> None:
        """Mark a step and the info as failed."""
        step_obj.result = False
        step_obj.msg = error
        info.status = "failed"
        info.error = error


__all__ = [
    "UpdateWikiTextProcessor",
]
