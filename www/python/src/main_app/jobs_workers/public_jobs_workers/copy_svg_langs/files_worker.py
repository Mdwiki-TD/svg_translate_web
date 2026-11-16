"""
Worker module for copy_svg_langs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mwclient.client import Site

from ....api_services import MwClientPage, UploadService
from ....api_services.files_service import DownloadAndSaveData, FilesService
from ....services.copysvg_wrapper import (
    ExtractResult,
    InjectResult,
    NestedStructureService,
    SvgInjector,
    SvgTranslationExtractor,
    TranslationMapping,
)
from ....utils.new_wikitext.other_versions import OtherVersionsUpdater
from .objects import (
    FilesProcessedItem,
    StepResult,
    SvgLangsConfig,
)

logger = logging.getLogger(__name__)


class OneFileProcessor:
    def __init__(self, config: SvgLangsConfig, files_service: FilesService, site: Site) -> None:
        self.config = config
        self.files_service = files_service
        self.site = site
        self.upload_service = UploadService(self.site)
        self.mapping: TranslationMapping | None = None
        self.upload_done = 0
        self.other_versions_updater = OtherVersionsUpdater()
        self.nested_processer = NestedStructureService(
            strategy="flatten",
        )

    def handle_nested_tag_repair_step(self, nested_step: StepResult, file_path: Path) -> tuple[int, bool]:

        detect_before = self.nested_processer.analyze_file(file_path)
        if len(detect_before) == 0:
            nested_step._update(msg="No nested tags found")
            # no nested tags, process to inject translations step
            return 0, True

        # Try to fix nested tags
        fixed = self.nested_processer.repair_file(file_path)
        if not fixed.success:
            nested_step._update(
                result=False,
                msg="Failed to fix nested tags",
                # details=detect_before,
            )
            # no nested tags fixed, break the file process
            return 0, False

        # Verify after fix
        verify = {
            "before": fixed.len_tags_before_fix,
            "after": fixed.len_tags_after_fix,
            "fixed": fixed.len_tags_fixed,
        }

        if fixed.len_tags_fixed == 0:
            nested_step._update(
                result=False,
                msg="No nested tags were fixed",
                details=verify,
            )

            # no nested tags fixed, break the file process
            return 0, False

        verify_fixed = fixed.len_tags_fixed

        nested_step._update(
            result=True,
            msg=f"Fixed {fixed.len_tags_fixed} nested tag(s)",
            details=verify,
        )

        # no nested tags remaining in the file, process to inject translations step
        return verify_fixed, True

    def inject_step_file(self, title_info: FilesProcessedItem, file_path: Path | str) -> Path | None:
        if not file_path:
            title_info.steps.inject._update(result=False, msg="No file path found")
            return None

        file_path = Path(file_path)
        output_file = self.config.output_dir / "translated" / file_path.name

        try:
            inject_result: InjectResult = SvgInjector().inject_one_file(
                file=file_path,
                translations=self.mapping,
                output_file=output_file,
                overwrite_translations=self.config.overwrite_translations,
            )
        except Exception:
            logger.exception("Failed during SVG translation injection")
            inject_result = InjectResult(
                result=False,
                msg="Failed during SVG translation injection",
                new_languages_count=None,
            )

        if inject_result.result is None:
            if inject_result.msg == "No changes":
                title_info.status = "skipped"

            title_info.steps.inject._update(
                result=None,
                msg=inject_result.msg,
            )
            return None

        if inject_result.result is False:
            title_info.steps.inject._update(
                result=False,
                msg=inject_result.msg,
            )
            return None

        if inject_result.result is not True:
            title_info.steps.inject._update(
                result=False,
                msg="Unknown error",
            )
            return None

        # inject_result.result is True definitely
        title_info.steps.translations._update(
            result=True,
            details={
                "new_list": inject_result.languages_after,
                "new": inject_result.new_languages_count or 0,
                "updated": inject_result.updated_translations or 0,
                "inserted": inject_result.inserted_translations or 0,
            },
        )

        title_info.steps.inject._update(
            result=True,
            msg=inject_result.msg,
            # details={
            #     "new_languages_count": inject_result.new_languages_count,
            #     "updated_translations": inject_result.updated_translations,
            #     "output_file": output_file,
            # },
        )

        return output_file

    def _upload_step(
        self,
        title_info: FilesProcessedItem,
        summary: str,
        new_path: Path | None,
    ) -> bool:
        # Check if settings upload_files option is disabled
        if self.config.upload_files is False:
            title_info.steps.upload._update(
                result=None,
                msg="skipped",
                details={"error": "Upload disabled from settings", "summary": summary},
            )
            title_info.status = "skipped"
            return False

        # Check if form upload input is enabled
        if not bool(self.config.upload):
            title_info.steps.upload._update(
                result=None,
                msg="skipped",
                details={"error": "Upload disabled", "summary": summary},
            )
            title_info.status = "skipped"
            return False

        if self.config.upload_limit > 0 and self.upload_done >= self.config.upload_limit:
            title_info.steps.upload._update(
                result=None,
                msg="skipped",
                details={"error": "Upload limit reached", "summary": summary},
            )
            title_info.status = "skipped"
            return False

        # Start uploading
        upload_result = self.upload_service.upload_svg(
            title_info.title,
            new_path,
            summary=summary,
        )
        if upload_result.ok is True:
            title_info.steps.upload._update(
                result=True,
                msg="File Successfully uploaded.",
                # details=upload.get("result", ""),
                details={"summary": summary},
            )

            self.upload_done += 1
            title_info.status = "success"
            # return True, all steps passed and upload is success
            return True

        error_and_details = {
            "error": upload_result.error or "",
            "error_details": upload_result.error_details,
            "summary": summary,
        }
        """
        "details": {
            "error": "fileexists-shared-forbidden",
            "error_details": "A file with this name already exists in the shared file repository. If you still want to upload your file, please go back and use a new name. [[File:Share_of_deaths_obesity,_AFG.svg|thumb|center|Share_of_deaths_obesity,_AFG.svg]]",
            "summary": "1 languages injected, 1 translations inserted from [[File:Death rate from obesity, World, 1990.svg]]"
          },
        """
        is_no_changes = upload_result.error in {"skipped", "fileexists-no-change"}
        if upload_result.ok is None and is_no_changes:
            title_info.steps.upload._update(
                result=None,
                msg=upload_result.msg or "",
                details=error_and_details,
            )
            title_info.status = "skipped"
            return False

        title_info.steps.upload._update(
            result=False,
            msg="Upload failed.",
            details=error_and_details,
        )
        title_info.status = "failed"
        title_info.error = upload_result.error or ""
        return False

    def _update_langs_step(self, title_info: FilesProcessedItem) -> bool:
        """Update the `Svg lang` template of the file description page after a successful upload.

        Mirrors the `Update langs` logic of the admin `update_wikitext` job (without the author update).

        A failure here does not fail the whole file (it is already uploaded), only this step
        is marked as failed/skipped and `title_info.status` is left untouched.

        Args:
            title_info: Item holding the per file steps results.

        Returns:
            True when the page was saved, False otherwise.
        """
        try:
            return self._run_update_langs(title_info)
        except Exception as exc:
            logger.exception("Error updating Svg lang template for %s", title_info.title)
            title_info.steps.update_langs._update(
                result=False,
                msg="Error updating langs",
                details={"error": str(exc)},
            )
            return False

    def _run_update_langs(self, title_info: FilesProcessedItem) -> bool:
        """Run the `Update langs` steps:
            1. load the file wikitext
            2. load the file languages (without `en`)
            3. merge them into `{{Svg lang|...}}` inside `|other versions=`
            4. save the page with summary `Insert Svg lang (de,fr,...)`
        """
        step = title_info.steps.update_langs
        page = MwClientPage(title_info.title, self.site)

        # ----------------------------------
        # Step 1 - load file wikitext
        text = page.get_text()
        if not text:
            step._update(result=False, msg=f"Could not retrieve text for {title_info.title}")
            return False

        # ----------------------------------
        # Step 2 - load file languages
        file_langs = self.files_service.get_file_languages(title_info.title)

        if file_langs.error:
            step._update(
                result=False,
                msg="Could not load file languages",
                details={"error": file_langs.error},
            )
            return False

        langs: list[str] = list(file_langs.langs or [])

        if "en" in langs:
            langs.remove("en")

        if not langs:
            step._update(
                result=None,
                msg="Skipped - no languages found",
                details={"langs": langs},
            )
            return False

        # ----------------------------------
        # Step 3 - update `Svg lang` template
        new_wikitext = self.other_versions_updater.add_svg_langs(
            text,
            langs,
            sort=False,
            delete_values=["en"],
        )

        if new_wikitext.strip() == text.strip():
            step._update(result=None, msg="Skipped - page content is already identical", details={"langs": langs})
            return False

        # ----------------------------------
        # Step 4 - save new text
        row = ",".join(langs)
        summary = f"Insert Svg lang ({row})"

        res = page.edit(new_wikitext, summary=summary)

        if res.get("success"):
            step._update(
                result=True,
                msg=f"Updated page: {title_info.title}",
                details={"summary": summary, "langs": langs, "newrevid": res.get("newrevid", 0)},
            )
            return True

        error = res.get("error", "Unknown error")
        step._update(
            result=False,
            msg="Failed to save page",
            details={"error": error, "summary": summary, "langs": langs},
        )
        return False

    def _upload_step_with_langs(
        self,
        title_info: FilesProcessedItem,
        summary: str,
        new_path: Path | None,
    ) -> bool:
        """Upload the file then update the `Svg lang` template of its description page."""
        uploaded = self._upload_step(title_info, summary, new_path)

        if not uploaded:
            # upload skipped or failed, nothing to update
            return False

        # The file is already uploaded, a failure of update_langs does not fail the file
        self._update_langs_step(title_info)

        return True

    def _create_language_summary(self, main_title: str, translation_details: dict[str, int]) -> str:
        new_count = translation_details.get("new", 0)
        updated = translation_details.get("updated", 0)
        inserted = translation_details.get("inserted", 0)

        file_name = main_title.removeprefix("File:")

        summary_list = []
        if new_count > 0:
            summary_list.append(f"{new_count} languages injected")

        if updated > 0:
            summary_list.append(f"{updated} translations Updated")

        if inserted > 0:
            summary_list.append(f"{inserted} translations inserted")

        if not summary_list:
            summary_list.append("Adding translations")

        summary = ", ".join(summary_list)

        summary += f" from [[File:{file_name}]]"

        return summary

    def get_file_path(self, title_info: FilesProcessedItem) -> None | str:
        down_step = title_info.steps.download
        try:
            file_data: DownloadAndSaveData = self.files_service.download_and_save(
                title=title_info.title,
                out_dir=self.config.output_dir_files,
                overwrite_download=self.config.overwrite_download,
            )
        except Exception as e:
            logger.exception("Error downloading SVG file")
            down_step._update(result=False, msg="Error downloading", details={"error": str(e)})
            title_info.status = "failed"
            title_info.error = "Error downloading"
            return None

        if file_data.result != "success":
            download_result = {"error": file_data.error or "download_failed"}
            down_step._update(result=False, msg="Failed to download file", details=download_result)
            title_info.status = "failed"
            title_info.error = "failed to download the file"

            if file_data.error:
                title_info.error += f", error: {file_data.error}"

            return None

        file_path: str | None = file_data.path
        if file_path:
            down_step._update(result=True, msg="Downloaded successfully", details={"path": file_path})
            return file_path

        down_step._update(result=False, msg="Failed to get file path", details={"path": file_path})
        title_info.status = "failed"
        title_info.error = "Failed to get file path"
        return None

    def extract_file_translations(self, title_info: FilesProcessedItem) -> None:
        if not self.config.merge_mapping_all_files:
            return

        file_path = Path(title_info.file_path)
        try:
            result: ExtractResult = SvgTranslationExtractor().extract(file_path)
        except Exception as e:
            logger.error("Error in stage translations")
            return

        mapping = result.mapping

        if result.success and mapping and not mapping.is_empty():
            self.update_translations(mapping)
            title_info.is_mapping_merged = True
            return

    # ------------------
    # Public API
    # ------------------

    def update_translations(self, mapping: TranslationMapping) -> None:
        if mapping.is_empty():
            return

        if self.mapping is None:
            self.mapping = mapping
            return

        self.mapping.merge(mapping, merge_keys=["new", "title_new"])

    def process_one_item(self, title_info: FilesProcessedItem, main_title: str) -> bool:
        # ----------------------------------------------
        # File step 1: download

        file_path_str: str | None = self.get_file_path(title_info)

        if not file_path_str:
            return False

        title_info.file_path = file_path_str
        file_path = Path(file_path_str)

        # ----------------------------------------------
        # File step 2: fix nested tags
        nested_step = title_info.steps.nested

        verify_fixed, no_nested_tags = self.handle_nested_tag_repair_step(nested_step, file_path)

        if not no_nested_tags:
            # no nested tags fixed, break the file process
            title_info.status = "failed"
            title_info.error = "nested tags"

            # We can't inject file that has nested tags
            title_info.steps.inject.msg = "skipped"
            title_info.steps.upload.msg = "skipped"
            title_info.steps.update_langs.msg = "skipped"
            return False

        # ----------------------------------------------
        # At this point, no nested tags remaining in the file
        # File step 3: log translations
        # File step 4: inject translations

        self.extract_file_translations(title_info)

        new_path: Path | None = self.inject_step_file(title_info, file_path)
        inject_result = title_info.steps.inject

        # ----------------------------------------------
        # File step 5: upload
        if inject_result.result is True:
            # inject success
            translation_details = title_info.steps.translations.details or {}
            summary = self._create_language_summary(main_title, translation_details)
            return self._upload_step_with_langs(title_info, summary, new_path)

        # ----------------------------------------------
        elif verify_fixed > 0:
            # Here we need to upload the orignal file because we fix nested tags.
            summary = f"{verify_fixed} nested tags fixed"
            return self._upload_step_with_langs(title_info, summary, file_path)

        # ----------------------------------------------
        # No nested tags were fixed
        # inject_result.result is one of (None/False)
        return False

    # ----
    # ----
    def _save_mapping(self, job_id: int) -> None:
        mapping_path = self.config.output_dir
        if mapping_path is None:
            return

        mapping_path = mapping_path.parent / f"{job_id}_all_files_mapping.json"

        if not self.mapping:
            logger.warning(f"No mapping to save for job {job_id}")
            return

        data = self.mapping.to_json()

        try:
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Error saving mapping: {e}")


__all__ = [
    "OneFileProcessor",
]
