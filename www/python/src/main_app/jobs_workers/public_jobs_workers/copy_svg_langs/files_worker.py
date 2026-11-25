"""
Worker module for copy_svg_langs.

Per-file pipeline (see `OneFileProcessor.process_one_item`):
    1. download -> 2. fix nested tags -> 3. extract translations
    -> 4. inject translations -> 5. upload -> 6. update `Svg lang`
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
from ....utils.new_wikitext.file_references import FileReferenceUpdater
from ....utils.new_wikitext.other_versions import OtherVersionsUpdater
from .objects import (
    FilesProcessedItem,
    StepResult,
    SvgLangsConfig,
)

logger = logging.getLogger(__name__)


class OneFileProcessor:
    def __init__(
        self,
        config: SvgLangsConfig,
        files_service: FilesService,
        site: Site,
        upload_service: UploadService | None = None,
        mw_client_cls: MwClientPage | None = None,
        svg_injector: SvgInjector | None = None,
        nested_processor: NestedStructureService | None = None,
    ) -> None:
        self.config = config
        self.files_service = files_service
        self.site = site
        self.mapping: TranslationMapping | None = None
        self.upload_done = 0
        self.other_versions_updater = OtherVersionsUpdater()

        self.nested_processor = nested_processor or NestedStructureService(strategy="flatten")
        self.upload_service = upload_service or UploadService(self.site)
        self.mw_client_cls = mw_client_cls or MwClientPage
        self.svg_injector = svg_injector or SvgInjector()

    # ==================================================================
    # Public API
    # ==================================================================

    def process_one_item(self, title_info: FilesProcessedItem, main_title: str) -> bool:
        """Run the whole pipeline for one file. Returns True only if the file was uploaded."""
        # Step 1: download
        file_path_str: str | None = self._step_download(title_info)
        if not file_path_str:
            return False

        title_info.file_path = file_path_str
        file_path = Path(file_path_str)

        # Step 2: fix nested tags
        verify_fixed, no_nested_tags = self._step_nested_tags(title_info.steps.nested, file_path)

        if not no_nested_tags:
            # a file with nested tags can't be injected
            title_info.status = "failed"
            title_info.error = "nested tags"
            title_info.steps.inject.msg = "skipped"
            title_info.steps.upload.msg = "skipped"
            title_info.steps.update_langs.msg = "skipped"
            return False

        # Step 3: log translations / Step 4: inject translations
        self._step_extract_translations(title_info)
        new_path: Path | None = self._step_inject(title_info, file_path)

        # Step 5 + 6: upload, then update `Svg lang`
        if new_path and title_info.steps.inject.result is True:
            translation_details = title_info.steps.translations.details or {}
            summary = self._create_language_summary(main_title, translation_details)
            return self._upload_and_update_langs(title_info, summary, new_path)

        if verify_fixed > 0:
            # injection did nothing, but nested tags were fixed: upload the original file
            summary = f"{verify_fixed} nested tags fixed"
            return self._upload_and_update_langs(title_info, summary, file_path)

        # inject result is None/False and nothing was fixed: nothing to upload
        title_info.steps.upload._update(result=None, msg="skipped")
        title_info.steps.update_langs._update(result=None, msg="skipped")
        return False

    def update_translations(self, mapping: TranslationMapping) -> None:
        """Merge a file mapping into the job-wide mapping."""
        if mapping.is_empty():
            return

        if self.mapping is None:
            self.mapping = mapping
            return

        self.mapping.merge(mapping, merge_keys=["new", "title_new"])

    def save_mapping(self, job_id: int) -> None:
        """Dump the job-wide mapping next to the output dir."""
        if self.config.output_dir is None:
            return

        if not self.mapping:
            logger.warning("No mapping to save for job %s", job_id)
            return

        mapping_path = self.config.output_dir.parent / f"{job_id}_all_files_mapping.json"

        try:
            with open(mapping_path, "w", encoding="utf-8") as f:
                json.dump(self.mapping.to_json(), f, ensure_ascii=False, indent=4)
        except Exception:
            logger.exception("Error saving mapping for job %s", job_id)

    # ==================================================================
    # Step 1 - download
    # ==================================================================

    def _step_download(self, title_info: FilesProcessedItem) -> str | None:
        step = title_info.steps.download
        try:
            file_data: DownloadAndSaveData = self.files_service.download_and_save(
                title=title_info.title,
                out_dir=self.config.output_dir_files,  # pyright: ignore[reportArgumentType]
                overwrite_download=self.config.overwrite_download,
            )
        except Exception as e:
            logger.exception("Error downloading SVG file")
            step._update(result=False, msg="Error downloading", details={"error": str(e)})
            title_info.status = "failed"
            title_info.error = "Error downloading"
            return None

        if file_data.result != "success":
            step._update(
                result=False,
                msg="Failed to download file",
                details={"error": file_data.error or "download_failed"},
            )
            title_info.status = "failed"
            title_info.error = "failed to download the file"
            if file_data.error:
                title_info.error += f", error: {file_data.error}"
            return None

        file_path = file_data.path
        if file_path:
            step._update(result=True, msg="Downloaded successfully", details={"path": file_path})
            return str(file_path)

        step._update(result=False, msg="Failed to get file path", details={"path": file_path})
        title_info.status = "failed"
        title_info.error = "Failed to get file path"
        return None

    # ==================================================================
    # Step 2 - fix nested tags
    # ==================================================================

    def _step_nested_tags(self, nested_step: StepResult, file_path: Path) -> tuple[int, bool]:
        """Returns `(number_of_fixed_tags, can_continue)`."""
        detect_before = self.nested_processor.analyze_file(file_path)
        if len(detect_before) == 0:
            nested_step._update(msg="No nested tags found")
            return 0, True

        fixed = self.nested_processor.repair_file(file_path)
        if not fixed.success:
            nested_step._update(result=False, msg="Failed to fix nested tags")
            return 0, False

        verify = {
            "before": fixed.len_tags_before_fix,
            "after": fixed.len_tags_after_fix,
            "fixed": fixed.len_tags_fixed,
        }

        if fixed.len_tags_fixed == 0:
            nested_step._update(result=False, msg="No nested tags were fixed", details=verify)
            return 0, False

        nested_step._update(
            result=True,
            msg=f"Fixed {fixed.len_tags_fixed} nested tag(s)",
            details=verify,
        )
        return fixed.len_tags_fixed, True

    # ==================================================================
    # Step 3 - extract translations
    # ==================================================================

    def _step_extract_translations(self, title_info: FilesProcessedItem) -> None:
        if not self.config.merge_mapping_all_files:
            return

        try:
            path = Path(title_info.file_path)  # pyright: ignore[reportArgumentType]
            result: ExtractResult = SvgTranslationExtractor().extract(path)
        except Exception:
            logger.exception("Error in stage translations")
            return

        mapping = result.mapping
        if result.success and mapping and not mapping.is_empty():
            self.update_translations(mapping)
            title_info.is_mapping_merged = True

    # ==================================================================
    # Step 4 - inject translations
    # ==================================================================

    def _step_inject(self, title_info: FilesProcessedItem, file_path: Path | str) -> Path | None:
        """Returns the translated file path, or None if nothing should be uploaded."""
        if not file_path:
            self._fail_inject(title_info, "No file path found")
            return None

        file_path = Path(file_path)
        output_file = self.config.output_dir / "translated" / file_path.name  # pyright: ignore[reportOptionalOperand]

        try:
            inject_result: InjectResult = self.svg_injector.inject_one_file(
                file=file_path,
                translations=self.mapping,  # pyright: ignore[reportArgumentType]
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
            title_info.steps.inject._update(result=None, msg=inject_result.msg or "")
            return None

        if inject_result.result is False:
            self._fail_inject(
                title_info,
                inject_result.msg,
                error=inject_result.msg or "Failed to inject translations",
            )
            return None

        if inject_result.result is not True:
            self._fail_inject(title_info, "Unknown error")
            return None

        # inject_result.result is True
        title_info.steps.translations._update(
            result=True,
            details={
                "new_list": inject_result.languages_after,
                "new": inject_result.new_languages_count or 0,
                "updated": inject_result.updated_translations or 0,
                "inserted": inject_result.inserted_translations or 0,
            },
        )
        title_info.steps.inject._update(result=True, msg=inject_result.msg or "")
        return output_file

    def _fail_inject(self, title_info: FilesProcessedItem, step_msg: str | None, error: str | None = None) -> None:
        title_info.steps.inject._update(result=False, msg=step_msg or "")
        title_info.mark_failed(error or step_msg or "Failed to inject translations")

    # ==================================================================
    # Step 5 + 6 - upload, then update `Svg lang`
    # ==================================================================

    def _upload_and_update_langs(
        self,
        title_info: FilesProcessedItem,
        summary: str,
        new_path: Path,
    ) -> bool:
        """Upload the file, then update the `Svg lang` template of its description page."""
        uploaded = self._step_upload(title_info, summary, new_path)

        if title_info.status != "failed":
            # a previous step (inject) may have left an error behind while the file was
            # still uploaded (nested tags fixed) or skipped
            title_info.error = None

        if not uploaded:
            return False

        # The file is already uploaded: a failure here does not fail the file
        self._step_update_langs(title_info)
        return True

    # ------------------------------------------------------------------
    # Step 5 - upload
    # ------------------------------------------------------------------

    def _step_upload(
        self,
        title_info: FilesProcessedItem,
        summary: str,
        new_path: Path,
    ) -> bool:
        if self.config.upload_files is False:
            return self._skip_upload(title_info, "Upload disabled from settings", summary)

        if not bool(self.config.upload):
            return self._skip_upload(title_info, "Upload disabled", summary)

        if self.config.upload_limit > 0 and self.upload_done >= self.config.upload_limit:
            return self._skip_upload(title_info, "Upload limit reached", summary)

        upload_result = self.upload_service.upload_svg(title_info.title, new_path, summary=summary)

        if upload_result.ok is True:
            title_info.steps.upload._update(
                result=True,
                msg="File Successfully uploaded.",
                details={"summary": summary},
            )
            self.upload_done += 1
            title_info.status = "success"
            return True

        # Example of a failure payload:
        #   {"error": "fileexists-shared-forbidden",
        #    "error_details": "A file with this name already exists in the shared file repository...",
        #    "summary": "1 languages injected, 1 translations inserted from [[File:...]]"}
        error_and_details = {
            "error": upload_result.error or "",
            "error_details": upload_result.error_details,
            "summary": summary,
        }

        is_no_changes = upload_result.error in {"skipped", "fileexists-no-change"}
        if upload_result.ok is None and is_no_changes:
            title_info.steps.upload._update(
                result=None,
                msg=upload_result.msg or "",
                details=error_and_details,
            )
            title_info.status = "skipped"
            return False

        title_info.steps.upload._update(result=False, msg="Upload failed.", details=error_and_details)
        title_info.status = "failed"
        title_info.error = upload_result.error or ""
        return False

    def _skip_upload(self, title_info: FilesProcessedItem, reason: str, summary: str) -> bool:
        title_info.steps.upload._update(
            result=None,
            msg="skipped",
            details={"error": reason, "summary": summary},
        )
        title_info.status = "skipped"
        return False

    # ------------------------------------------------------------------
    # Step 6 - update `Svg lang`
    # ------------------------------------------------------------------

    def _step_update_langs(self, title_info: FilesProcessedItem) -> bool:
        """Update the `{{Svg lang|...}}` template inside `|other versions=` of the description page.

        Mirrors the `Update langs` logic of the admin `update_wikitext` job (without the author update).
        A failure here never fails the file (it is already uploaded): only this step is marked.

        Returns:
            True when the page was saved, False otherwise.
        """
        step = title_info.steps.update_langs
        # titles are stored without the namespace prefix, the description page needs `File:`
        file_title = FileReferenceUpdater.ensure_prefix(title_info.title)

        try:
            page = self.mw_client_cls.load(file_title, self.site)

            text = page.get_text()
            if not text:
                step._update(result=False, msg=f"Could not retrieve text for {file_title}")
                return False

            langs, error = self._load_langs(file_title)
            if error:
                step._update(result=False, msg="Could not load file languages", details={"error": error})
                return False

            if not langs:
                step._update(result=None, msg="Skipped - no languages found", details={"langs": langs})
                return False

            new_wikitext = self.other_versions_updater.add_svg_langs(
                text,
                langs,
                sort=False,
                values_to_delete=["en"],
            )
            if new_wikitext.strip() == text.strip():
                step._update(
                    result=None,
                    msg="Skipped - page content is already identical",
                    details={"langs": langs},
                )
                return False

            return self._save_langs_page(step, page, file_title, new_wikitext, langs)

        except Exception as exc:
            logger.exception("Error updating Svg lang template for %s", title_info.title)
            step._update(result=False, msg="Error updating langs", details={"error": str(exc)})
            return False

    def _load_langs(self, file_title: str) -> tuple[list[str], str | None]:
        """Returns `(langs_without_en, error)`."""
        file_langs = self.files_service.get_file_languages(file_title)
        if file_langs.error:
            return [], file_langs.error
        return [lang for lang in (file_langs.langs or []) if lang != "en"], None

    def _save_langs_page(
        self,
        step: StepResult,
        page: MwClientPage,
        file_title: str,
        new_wikitext: str,
        langs: list[str],
    ) -> bool:
        summary = f"Insert Svg lang ({','.join(langs)})"
        res = page.edit(new_wikitext, summary=summary)

        if res.get("success"):
            step._update(
                result=True,
                msg=f"Updated page: {file_title}",
                details={"summary": summary, "langs": langs, "newrevid": res.get("newrevid", 0)},
            )
            return True

        step._update(
            result=False,
            msg="Failed to save page",
            details={"error": res.get("error", "Unknown error"), "summary": summary, "langs": langs},
        )
        return False

    # ==================================================================
    # Helpers
    # ==================================================================

    def _create_language_summary(self, main_title: str, translation_details: dict[str, int]) -> str:
        new_count = translation_details.get("new", 0)
        updated = translation_details.get("updated", 0)
        inserted = translation_details.get("inserted", 0)

        parts = []
        if new_count > 0:
            parts.append(f"{new_count} languages injected")
        if updated > 0:
            parts.append(f"{updated} translations Updated")
        if inserted > 0:
            parts.append(f"{inserted} translations inserted")
        if not parts:
            parts.append("Adding translations")

        file_name = main_title.removeprefix("File:")
        return f"{', '.join(parts)} from [[File:{file_name}]]"


__all__ = [
    "OneFileProcessor",
]
