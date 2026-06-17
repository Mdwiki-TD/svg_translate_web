"""
Worker module for copy_svg_langs_per_file.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any, Tuple

import requests
from mwclient.client import Site

from ....api_services import create_commons_session, get_user_site
from ....api_services.files_service import download_svg_file, upload_fixed_svg
from ....config import settings
from ....shared.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
    detect_nested_tags,
    fix_nested_tags,
    verify_fix,
)
from ...base_worker_object import BaseObjectsJobWorker
from .objects import CopySvgLangsPerFileWorkerObject, FilesProcessedItem, FileSteps, StepResult
from .steps import (
    InjectResult,
    extract_text_step,
    extract_titles_step,
    extract_translations_step,
    inject_step_one_file,
)

logger = logging.getLogger(__name__)


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
        self.result: CopySvgLangsPerFileWorkerObject = CopySvgLangsPerFileWorkerObject()
        self.result.job_id = self.job_id
        self.args = args or {}
        self.result.args = self.args

        self.upload_done = 0
        self.title = self.args.get("title")
        self.overwrite_downloads = bool(self.args.get("overwrite_downloads"))
        self.overwrite_translations = bool(self.args.get("overwrite"))

        upload_limit = self.args.get("upload_limit") or 0
        self.upload_limit = upload_limit if isinstance(upload_limit, int) else 0

        self.output_dir = self._compute_output_dir(self.title)
        self.files_dict: list[str] = []
        self.site: Site | None = None
        self.session: requests.Session | None = None

        self.text: str = ""
        self.main_title: str = ""
        self.titles: list[str] = []
        self.translations: dict[str, str] = {}

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "copy_svg_langs_per_file"

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
            stage.status = "Cancelled"
            return False

        stage.status = "Running"
        self._save_progress()

        try:
            step_result = extract_titles_step(
                self.text,
                manual_main_title=self.args.get("manual_main_title"),
            )

        except Exception as e:
            logger.exception("Error in stage titles")
            stage.status = "Failed"
            stage.message = str(e)
            self.result.status = "failed"

            return False

        if step_result.get("message"):
            stage.message = step_result["message"]

        if step_result.get("success"):
            stage.status = "Completed"

            self.main_title = step_result["main_title"]
            self.titles = list(step_result["titles"])

            return True

        stage.status = "Failed"
        stage.message = step_result.get("error", "Unknown error")
        self.result.status = "failed"
        return False

    def _extract_translations_step(self) -> bool | None:
        stage = self.result.stages.translations
        stage.status = "Running"

        step_result = extract_translations_step(
            self.main_title,
            self.output_dir / "files",
        )
        new_translations = step_result.get("translations", {})

        if step_result.get("success") and new_translations:
            stage.status = "Completed"
            self.translations = new_translations
            return True

        stage.status = "Failed"
        stage.message = step_result.get("error") or step_result.get("message") or "Unknown error"
        self.result.status = "failed"

        return False

    def _extract_text_step(self) -> bool | None:
        stage = self.result.stages.text
        stage.status = "Running"

        if self.is_cancelled():
            stage.status = "Cancelled"
            return False

        step_result = extract_text_step(
            self.title,
            self.site,
        )
        text = step_result.get("text", "")

        if step_result.get("success") and text:
            stage.status = "Completed"
            self.text = text
            return True

        stage.status = "Failed"
        stage.message = step_result.get("error") or "Unknown error"
        self.result.status = "failed"

        return False

    def process(self) -> CopySvgLangsPerFileWorkerObject:
        """Execute the full pipeline."""
        if not self.title:
            logger.error("No title found")
            self.result.status = "failed"
            return self.result

        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning("Job %s: No site authentication available", self.job_id)
            self.log_no_site_error()
            return self.result

        self.session = create_commons_session(settings.other.user_agent)
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

        # Initialize files_processed
        per_item = self.get_priority(len(self.titles))

        for n, title in enumerate(self.titles, start=1):
            logger.info("Job %s: Processing title %d/%d: %s", self.job_id, n, len(self.titles), title)

            if self.is_cancelled():
                logger.info("Job %s: Cancellation detected, stopping.", self.job_id)
                break

            ok, title_info = self._process_one(title)

            self.result.files_processed.append(title_info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self._save_progress()

        return self.result

    def inject_step_file(
        self,
        title_info: FilesProcessedItem,
    ) -> Tuple[StepResult, None | str]:

        file_path = Path(title_info.file_path)
        output_file = self.output_dir / "translated" / file_path.name

        inject_result: InjectResult = inject_step_one_file(
            file_path,
            self.translations,
            output_file,
            overwrite=self.overwrite_translations,
        )

        if inject_result.result is None:
            step_result = StepResult(
                result=None,
                msg=inject_result.msg,
            )
            return step_result, None

        if inject_result.result is False:
            step_result = StepResult(
                result=False,
                msg=inject_result.msg,
            )
            return step_result, None

        step_result = StepResult(
            result=True,
            msg=inject_result.msg,
        )
        return step_result, output_file

    def _process_one(self, title: str) -> bool:
        self.result.summary.processed += 1

        title_info = FilesProcessedItem(
            title=title,
            file_path=None,
            file_path_to_upload=None,
            status="pending",
            error=None,
            steps=FileSteps(
                download=StepResult(result=None, msg=""),
                nested=StepResult(result=None, msg=""),
                inject=StepResult(result=None, msg=""),
                upload=StepResult(result=None, msg=""),
            ),
        )
        # ----------------------------------------------
        # Stage 4: download SVG files

        try:
            download = download_svg_file(
                title,
                self.output_dir / "files",
                session=self.session,
            )
        except Exception as e:
            logger.exception("Error downloading SVG file")
            title_info.steps.download = StepResult(result=False, msg="Error downloading", details={"error": str(e)})
            return False

        if not download.get("ok"):
            title_info.steps.download = StepResult(result=False, msg="Failed to download file", details=download)
            return False

        title_info.steps.download = StepResult(result=True, msg="Downloaded successfully", details=download)

        file_path = download.get("path")
        title_info.file_path = file_path

        # ----------------------------------------------
        # Stage 5: Analyze And Fix Nested Files

        detect_before: DetectionResult = detect_nested_tags(file_path)

        if detect_before.count == 0:
            title_info.steps.nested = StepResult(result=None, msg="No nested tags found")
        else:
            # Try to fix nested tags
            if not fix_nested_tags(file_path):
                title_info.steps.nested = StepResult(
                    result=False,
                    msg="Failed to fix nested tags",
                    details=detect_before.to_dict(),
                )
                # We can't inject file that has nested tags
                title_info.steps.inject.msg = "skipped"
                title_info.steps.upload.msg = "skipped"
                return False

            verify: VerificationResult = verify_fix(file_path, detect_before.count)

            if verify.fixed == 0:
                title_info.steps.nested = StepResult(
                    result=False,
                    msg="No nested tags were fixed",
                    details=verify.to_dict(),
                )
                # We can't inject file that has nested tags
                title_info.steps.inject.msg = "skipped"
                title_info.steps.upload.msg = "skipped"
                return False

        # ----------------------------------------------
        # At this point, no nested tags remaining in the file
        # Stage 6: Inject translations

        inject_result, new_path = self.inject_step_file(title_info)
        if not inject_result.result:
            return False

        title_info.file_path_to_upload = new_path
        # ----------------------------------------------
        # Stage 7: Upload

        if not bool(self.args.get("upload")):
            title_info.steps.upload = StepResult(
                result=None,
                msg="skipped",
                details={"error": "Upload disabled"},
            )
            title_info.status = "skipped"
            return False

        if self.upload_done >= self.upload_limit:
            title_info.steps.upload = StepResult(
                result=None,
                msg="skipped",
                details={"error": "Upload limit reached"},
            )
            title_info.status = "skipped"
            return False

        # Start uploading
        upload = upload_fixed_svg(
            title_info.title,
            title_info.file_path_to_upload,
            verify.fixed,
            self.site,
        )
        upload_success = upload.get("ok")
        upload_error = upload.get("error") or ""
        upload_msg = upload.get("msg") or ""

        if upload_success is True:
            title_info.steps.upload = StepResult(
                result=True,
                msg=f"Successfully fixed {verify.fixed} nested tag(s) and file uploaded.",
                details=upload.get("result", ""),
            )

            self.upload_done += 1
            title_info.status = "completed"
            # return True, all steps passed and upload is success
            return True

        error_and_details = {
            "error": upload_error,
            "error_details": upload.get("error_details", ""),
        }

        if upload_success is None and upload_error == "skipped":
            title_info.steps.upload = StepResult(
                result=None,
                msg=upload_msg,
                details=error_and_details,
            )
            return False

        title_info.error = upload_error
        title_info.steps.upload = StepResult(
            result=False,
            msg=f"Fixed {verify.fixed} nested tag(s), but upload failed.",
            details=error_and_details,
        )
        return False


# --- main pipeline --------------------------------------------
def copy_svg_langs_per_file_worker_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """Entry point for the background job."""

    worker = CopySvgLangsWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "copy_svg_langs_per_file_worker_entry",
    "CopySvgLangsWorker",
]
