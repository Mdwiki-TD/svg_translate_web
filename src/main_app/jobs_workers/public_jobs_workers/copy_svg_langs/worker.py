"""
Worker module for copy_svg_langs.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any

import requests
from mwclient.client import Site

from ....api_services import create_commons_session, download_one_file, upload_fixed_svg
from ....config import settings
from ....shared.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
    detect_nested_tags,
    fix_nested_tags,
    verify_fix,
)
from ...base_worker import BaseObjectsJobWorker
from .objects import CopySvgLangsWorkerObject, FilesProcessedItem, FileSteps, StepResult
from .steps import (
    ExtractResult,
    InjectResult,
    extract_from_path,
    extract_text_step,
    extract_titles_step,
    inject_step_one_file,
)

logger = logging.getLogger(__name__)


class OneFileProcessor:

    def __init__(self, site: Site | None, output_dir: Path, args: dict[str, Any]):
        self.site = site
        self.output_dir = output_dir
        self.output_dir_files = (self.output_dir / "files") if self.output_dir else None

        self.args = args

        upload_limit = self.args.get("upload_limit") or 0
        self.upload_limit = upload_limit if isinstance(upload_limit, int) else 0

        self.overwrite_translations = bool(self.args.get("overwrite"))

        self.session: requests.Session = create_commons_session(settings.other.user_agent)
        self.translations: dict[str, str] = {}
        self.upload_done = 0

    def update_translations(self, translations: dict[str, str]) -> None:
        self.translations.update(translations)

    def _process_one_item(self, title: str, title_info: FilesProcessedItem, main_title: str) -> bool:
        # ----------------------------------------------
        # File step 1: download

        file_path_str: str | None = self.get_download_path(title, title_info)

        if not file_path_str:
            return False

        title_info.file_path = file_path_str

        file_path = Path(file_path_str)

        # ----------------------------------------------
        # File step 2: fix nested tags

        verify_fixed, no_nested_tags = self.handle_nested_tag_repair_step(title_info, file_path)

        if not no_nested_tags:
            # no nested tags fixed, break the file process
            title_info.status = "failed"

            # We can't inject file that has nested tags
            title_info.steps.inject.msg = "skipped"
            title_info.steps.upload.msg = "skipped"
            return False

        # ----------------------------------------------
        # At this point, no nested tags remaining in the file
        # File step 3: log translations
        # File step 4: inject translations

        new_path: Path | None = self.inject_step_file(title_info, file_path)
        inject_result = title_info.steps.inject

        # ----------------------------------------------
        # File step 5: upload

        if inject_result.result is True:
            # inject success
            new_languages_count = inject_result.details.get("new_languages", 0) if inject_result.details else 0
            summary = self._create_language_summary(main_title, new_languages_count)
            return self._upload_step(title_info, summary, new_path)

        # ----------------------------------------------
        if verify_fixed > 0:
            # Here we need to upload the orignal file because we fix nested tags.
            summary = f"{verify_fixed} nested tags fixed"
            return self._upload_step(title_info, summary, file_path)

        # No nested tags were fixed, and inject failed
        return False

    def handle_nested_tag_repair_step(self, title_info: FilesProcessedItem, file_path: Path) -> tuple[int, bool]:

        detect_before: DetectionResult = detect_nested_tags(file_path)
        if detect_before.count == 0:
            title_info.steps.nested._update(msg="No nested tags found")
            # no nested tags, process to inject translations step
            return 0, True

        # Try to fix nested tags
        if not fix_nested_tags(file_path):
            title_info.steps.nested._update(
                result=False,
                msg="Failed to fix nested tags",
                details=detect_before.to_dict(),
            )
            # no nested tags fixed, break the file process
            return 0, False

        verify: VerificationResult = verify_fix(file_path, detect_before.count)

        if verify.fixed == 0:
            title_info.steps.nested._update(
                result=False,
                msg="No nested tags were fixed",
                details=verify.to_dict(),
            )
            # no nested tags fixed, break the file process
            return 0, False

        verify_fixed = verify.fixed

        title_info.steps.nested._update(
            result=True,
            msg=f"Fixed {verify.fixed} nested tag(s)",
            details=verify.to_dict(),
        )

        # no nested tags remaining in the file, process to inject translations step
        return verify_fixed, True

    def inject_step_file(self, title_info: FilesProcessedItem, file_path: Path | str) -> Path | None:
        if not file_path:
            title_info.steps.inject._update(result=False, msg="No file path found")
            return None

        file_path = Path(file_path)
        output_file = self.output_dir / "translated" / file_path.name

        inject_result: InjectResult = inject_step_one_file(
            file_path,
            self.translations,
            output_file,
            overwrite=self.overwrite_translations,
        )

        if inject_result.result is None:
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

        title_info.steps.translations._update(
            result=True,
            details={
                "new_list": inject_result.new_languages_list,
                "new": inject_result.new_languages_count or 0,
                "updated": inject_result.updated_translations or 0,
            },
        )
        title_info.steps.inject._update(
            result=True,
            msg=inject_result.msg,
            # details={
            #     "new_languages": inject_result.new_languages,
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
        if self.args.get("upload_files") is False:
            title_info.steps.upload._update(
                result=None,
                msg="skipped",
                details={"error": "Upload disabled from settings"},
            )
            title_info.status = "skipped"
            return False

        # Check if form upload input is enabled
        if not bool(self.args.get("upload")):
            title_info.steps.upload._update(
                result=None,
                msg="skipped",
                details={"error": "Upload disabled"},
            )
            title_info.status = "skipped"
            return False

        if self.upload_limit > 0 and self.upload_done >= self.upload_limit:
            title_info.steps.upload._update(
                result=None,
                msg="skipped",
                details={"error": "Upload limit reached"},
            )
            title_info.status = "skipped"
            return False

        # Start uploading
        upload = upload_fixed_svg(
            title_info.title,
            new_path,
            self.site,
            summary=summary,
        )
        upload_success = upload.get("ok")
        upload_error = upload.get("error") or ""
        upload_msg = upload.get("msg") or ""
        error_details = upload.get("error_details", "")

        if upload_success is True:
            title_info.steps.upload._update(
                result=True,
                msg="File Successfully uploaded.",
                # details=upload.get("result", ""),
            )

            self.upload_done += 1
            title_info.status = "success"
            # return True, all steps passed and upload is success
            return True

        error_and_details = {
            "error": upload_error,
            "error_details": error_details,
        }

        is_no_changes = upload_error in {"skipped", "fileexists-no-change"}
        if upload_success is None and is_no_changes:
            title_info.steps.upload._update(
                result=None,
                msg=upload_msg,
                details=error_and_details,
            )
            title_info.status = "skipped"
            return False

        title_info.error = upload_error
        title_info.steps.upload._update(
            result=False,
            msg="Upload failed.",
            details=error_and_details,
        )
        title_info.status = "failed"
        return False

    def _create_language_summary(self, main_title: str, new_languages_count: int) -> str:
        file_name = main_title.removeprefix("File:")
        main_title_link = f"[[File:{file_name}]]"

        summary = (
            f"Adding {new_languages_count} languages translations from {main_title_link}"
            if new_languages_count > 0
            else f"Adding translations from {main_title_link}"
        )

        return summary

    def get_download_path(self, title: str, title_info: FilesProcessedItem):
        down_step = title_info.steps.download
        try:
            file_data = download_one_file(
                title=title,
                out_dir=self.output_dir_files,
                overwrite=True,
                session=self.session,
            )
        except Exception as e:
            logger.exception("Error downloading SVG file")
            down_step._update(result=False, msg="Error downloading", details={"error": str(e)})
            title_info.status = "failed"
            return None

        if file_data.get("result") != "success":
            download_result = {
                "ok": False,
                "path": None,
                "error": "download_failed",
                "details": file_data,
            }
            down_step._update(result=False, msg="Failed to download file", details=download_result)
            title_info.status = "failed"
            return None

        file_path: str | None = file_data.get("path")

        download_result = {
            "ok": True,
            "path": file_path,
            "error": None,
            "details": {},
        }

        if file_path:
            down_step._update(result=True, msg="Downloaded successfully", details=download_result)
            return file_path

        down_step._update(result=False, msg="Failed to get file path", details=download_result)
        title_info.status = "failed"
        return None


class CopySvgLangsWorker(BaseObjectsJobWorker):
    """
    Worker for copying SVG translations from a main file to its versions.
    """

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.user: dict[str, Any] = user

        super().__init__(job_id, user, cancel_event)
        self.result: CopySvgLangsWorkerObject = CopySvgLangsWorkerObject()
        self.result.job_id = self.job_id
        self.args = args or {}
        self.result.args = self.args

        self.title = self.args.get("title")
        self.limit_items = self.args.get("limit_items") or 0

        self.output_dir = self._compute_output_dir(self.title)
        self.output_dir_files = (self.output_dir / "files") if self.output_dir else None

        self.files_dict: list[str] = []
        self.site: Site | None = None

        self.text: str = ""
        self.main_title: str = ""
        self.titles: list[str] = []
        self.translations: dict[str, str] = {}
        self.files_processor = OneFileProcessor(self.site, self.output_dir, self.args)

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "copy_svg_langs"

    def _apply_limits(self, titles: list[str]) -> list[str]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(titles) > _limit:
            logger.info("Job %s: limiting from %d to %d page", self.job_id, len(titles), _limit)
            return titles[:_limit]

        return titles

    def _compute_output_dir(self, title: str) -> Path:
        if not title:
            return None

        name = Path(title).name
        slug = re.sub(r"[^A-Za-z0-9._\- ]+", "_", str(name)).strip("._") or "untitled"
        slug = slug.replace(" ", "_").lower()
        out = Path(settings.paths.svg_data) / slug
        out.mkdir(parents=True, exist_ok=True)

        out_translated = out / "translated"
        out_translated.mkdir(parents=True, exist_ok=True)

        out_dir_main = out / "files"
        out_dir_main.mkdir(parents=True, exist_ok=True)

        return out

    def _save_files_stats(self, stats_data) -> None:
        files_stats_path = self.output_dir / "files_stats.json"
        try:
            with open(files_stats_path, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=4, ensure_ascii=False)

        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Error saving json: {e!s}, path: {files_stats_path!s}")
        except Exception:
            logger.exception(f"Unexpected error saving json, path: {files_stats_path!s}")

    def _extract_titles_step(self) -> bool:
        stage = self.result.stages.titles

        if self.is_cancelled():
            stage.status = "cancelled"
            return False

        stage.status = "running"
        self._save_progress()

        try:
            step_result = extract_titles_step(
                self.text,
                manual_main_title=self.args.get("manual_main_title"),
            )

        except Exception as e:
            logger.exception("Error in stage titles")
            stage.status = "failed"
            stage.message = str(e)
            self.result.status = "failed"

            return False

        if step_result.get("message"):
            stage.message = step_result["message"]

        if step_result.get("success"):
            stage.status = "completed"

            self.main_title = step_result["main_title"]
            self.result.main_title = self.main_title
            self.titles = list(step_result["titles"])
            self.titles.sort()

            return True

        stage.status = "failed"
        stage.message = step_result.get("error", "Unknown error")
        self.result.status = "failed"
        return False

    def _extract_translations_step(self) -> bool | None:
        stage = self.result.stages.translations
        stage.status = "running"
        output_dir_main = self.output_dir_files

        main_file_download = download_one_file(title=self.main_title, out_dir=output_dir_main, overwrite=True)

        if not main_file_download.get("path"):
            error = f"Error when downloading main file: {self.main_title}"
            logger.error(error)
            stage.status = "failed"
            stage.message = error
            self.result.status = "failed"

            return False

        main_title_path = main_file_download["path"]

        try:
            step_result: ExtractResult = extract_from_path(main_title_path)
        except Exception as e:
            logger.exception("Error in stage translations")
            stage.status = "failed"
            stage.message = str(e)
            self.result.status = "failed"
            return False

        file_translations = step_result.translations or {}

        new_translations = file_translations.get("new", {})

        languages = sorted(
            {lang for entry in file_translations.get("new", {}).values() if isinstance(entry, dict) for lang in entry}
        )
        self.result.translations = self._render_new_translations(new_translations, languages)
        self.result.languages = languages

        if step_result.success and file_translations:
            stage.status = "completed"
            # stage.message = f"Loaded {len(file_translations)} translations from (File:{self.main_title})"
            stage.message = step_result.message or f"Loaded translations from (File:{self.main_title})"
            self.translations = file_translations
            self.files_processor.update_translations(file_translations)
            return True

        stage.status = "failed"
        stage.message = step_result.error or "Unknown error"
        self.result.status = "failed"

        return False

    def _extract_text_step(self) -> bool | None:
        stage = self.result.stages.text
        stage.status = "running"

        if self.is_cancelled():
            stage.status = "cancelled"
            return False

        try:
            step_result = extract_text_step(
                self.title,
                self.site,
            )
        except Exception as e:
            logger.exception("Error in stage text")
            stage.status = "failed"
            stage.message = str(e)
            self.result.status = "failed"
            return False

        text = step_result.get("text", "")

        if step_result.get("success") and text:
            stage.status = "completed"
            stage.message = "Text extracted successfully"
            self.text = text
            return True

        stage.status = "failed"
        stage.message = step_result.get("error") or "Unknown error"
        self.result.status = "failed"

        return False

    def _process_one_item(self, title: str, title_info: FilesProcessedItem, main_title: str) -> bool:
        return self.files_processor._process_one_item(title, title_info, main_title)

    def process(self) -> CopySvgLangsWorkerObject:
        """Execute the full pipeline."""
        if not self._check_site():
            return self.result

        # update site after calling _check_site
        self.files_processor.site = self.site

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
        # extract titles runs before extract_translations because it returns self.main_title
        # which is used in extract_translations

        if not self._extract_titles_step():
            return self.result

        # ----------------------------------------------
        # Stage 3: Extract Translations

        if not self._extract_translations_step():
            return self.result

        processfiles_stage = self.result.stages.processfiles

        self.result.summary.total = len(self.titles)
        title_to_work = self._apply_limits(self.titles)

        per_item = self.get_priority(len(title_to_work))
        processfiles_stage.status = "running"

        for n, title in enumerate(title_to_work, start=1):
            processfiles_stage.message = f"Processing files {n}/{len(title_to_work)}"
            logger.info("Job %s: Processing title %d/%d: %s", self.job_id, n, len(title_to_work), title)

            if self.is_cancelled():
                logger.info("Job %s: Cancellation detected, stopping.", self.job_id)
                processfiles_stage.status = "cancelled"
                break

            title_info = FilesProcessedItem(
                title=title,
                file_path=None,
                status="pending",
                error=None,
                steps=FileSteps(
                    download=StepResult(msg=""),
                    nested=StepResult(msg=""),
                    translations=StepResult(msg="", details={"new": 0, "updated": 0, "new_list": []}),
                    inject=StepResult(msg=""),
                    upload=StepResult(msg=""),
                ),
            )
            self.result.summary.processed += 1
            ok = self._process_one_item(title, title_info, self.main_title)

            if title_info.status.lower() in ["pending", "running"]:
                title_info.status = "completed"

            if title_info.status == "success":
                self.result.files_success.append(title_info)

            elif title_info.status == "skipped":
                self.result.files_skipped.append(title_info)

            elif title_info.status == "failed":
                self.result.files_failed.append(title_info)
            else:
                self.result.files_processed.append(title_info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self._save_progress()

        if processfiles_stage.status in ["pending", "running"]:
            processfiles_stage.status = "completed"

        return self.result

    def _render_new_translations(self, translations: dict[str, Any], languages: list[str]) -> list[dict[str, str]]:
        data = []

        for en, row in translations.items():
            # empty data
            if not row:
                continue
            item = {"en": en}
            for lang in languages:
                item[lang] = row.get(lang, "")
            data.append(item)

        return data


__all__ = [
    "CopySvgLangsWorker",
]
