"""
Worker module for copy_svg_langs_per_file.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any, Callable

import requests
from mwclient.client import Site

from ....api_services import create_commons_session, get_user_site
from ....config import settings
from ...base_worker_object import BaseObjectsJobWorker
from .objects import CopySvgLangsWorkerObject, FilesProcessedItem, StageDetail, StepResult
from .steps import (
    download_step,
    extract_text_step,
    extract_titles_step,
    extract_translations_step,
    fix_nested_step,
    inject_step,
    upload_step,
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
        self.result: CopySvgLangsWorkerObject = CopySvgLangsWorkerObject()
        self.result.job_id = self.job_id
        self.args = args or {}
        self.result.args = self.args

        self.upload_limit = self.args.get("upload_limit") or 0
        self.title = self.args.get("title")

        self.output_dir = self._compute_output_dir(self.title)
        self.files_dict: list[str] = []
        self.site: Site | None = None
        self.session: requests.Session | None = None

        self.overwrite_downloads = bool(self.args.get("overwrite_downloads"))
        self.text: str = ""
        self.main_title: str = ""
        self.titles: list[str] = []
        self.translations: dict[str, str] = {}
        self.nested_data: dict[str, str] = {}
        self.nested_results: dict[str, str] = {}
        self.inject_data: dict[str, Any] = {}
        self.files_to_upload: dict[str, str] = {}

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

        return out

    def _is_cancelled(self, stage: StageDetail) -> bool:
        if self.is_cancelled():
            stage.status = "Cancelled"
            return True

        return False

    def log_upload_error(self, _msg, result, status) -> None:
        self.result.stages.upload.status = status
        self.result.stages.upload.message = _msg

        for _, item in self.result.files_processed.items():
            if item.status != "failed":
                item.steps.upload = StepResult(
                    result=result,
                    msg=_msg,
                )
                item.status = status
                item.error = _msg

    def _save_files_stats(self, stats_data) -> None:
        files_stats_path = self.output_dir / "files_stats.json"
        try:
            with open(files_stats_path, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=4, ensure_ascii=False)

        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Error saving json: {e!s}, path: {files_stats_path!s}")
        except Exception:
            logger.exception(f"Unexpected error saving json, path: {files_stats_path!s}")

    def _run_stage(
        self,
        stage: StageDetail,
        step_func: Callable[[], dict[str, Any]],  # Accepts a zero-argument callable that returns a dict
        run_after_func: Callable[[], None] | None = None,
    ) -> bool:
        """Run a single stage and update result."""
        stage_name = stage.name

        if self._is_cancelled(stage):
            stage.status = "Cancelled"
            return False

        stage.status = "Running"
        self._save_progress()

        try:
            # Call the lambda / callback directly without passing args
            step_result = step_func()
            stage.data = step_result

            if step_result.get("message"):
                stage.message = step_result["message"]

            if step_result.get("success"):
                stage.status = "Completed"
                if "summary" in step_result and not stage.message:
                    summary = step_result["summary"]
                    if isinstance(summary, dict):
                        stage.message = ", ".join(f"{k}: {v}" for k, v in summary.items())

                if run_after_func:
                    run_after_func()
                return True
            else:
                stage.status = "Failed"
                stage.message = step_result.get("error", "Unknown error")
                self.result.status = "failed"
                return False

        except Exception as e:
            logger.exception(f"Error in stage {stage_name}")
            stage.status = "Failed"
            stage.message = str(e)
            self.result.status = "failed"
            return False

    def _extract_step(self) -> bool | None:
        data = extract_text_step(
            self.title,
            self.site,
        )
        return data

    def text_run_after(self) -> None:
        self.text = self.result.stages.text.data["text"]
        # clean up
        self.result.stages.text.data["text"] = ""

    def process(self) -> CopySvgLangsWorkerObject:
        """Execute the full pipeline."""

        self.session = create_commons_session(settings.other.user_agent)
        self.site = get_user_site(self.user)

        if not self.title:
            logger.error("No title found")
            self.result.status = "failed"
            return self.result

        self.result.title = self.title
        # ----------------------------------------------
        # Stage 1: Extract Text

        if not self._run_stage(
            self.result.stages.text,
            step_func=self._extract_step,
        ):
            return self.result

        self.text_run_after()

        # ----------------------------------------------
        # Stage 2: Extract Titles
        def titles_run_after() -> None:
            titles_data = self.result.stages.titles.data
            self.main_title = titles_data["main_title"]
            self.titles = list(titles_data["titles"])

            # clean up
            self.result.stages.titles.data["titles"] = []

        if not self._run_stage(
            self.result.stages.titles,
            step_func=lambda: extract_titles_step(
                self.text,
                manual_main_title=self.args.get("manual_main_title"),
            ),
            run_after_func=titles_run_after,
        ):
            return self.result

        # Initialize files_processed

        for title in self.titles:
            self.result.files_processed[title] = FilesProcessedItem(
                title=title,
                status="pending",
                error=None,
            )

        # ----------------------------------------------
        # Stage 3: Extract Translations
        output_dir_main = self.output_dir / "files"
        output_dir_main.mkdir(parents=True, exist_ok=True)

        def translations_run_after() -> None:
            data = self.result.stages.translations.data
            self.translations = data["translations"]
            # self.result.stages.translations.message = data["message"]

        if not self._run_stage(
            self.result.stages.translations,
            step_func=lambda: extract_translations_step(
                self.main_title,
                output_dir_main,
            ),
            run_after_func=translations_run_after,
        ):
            return self.result
        # ----------------------------------------------
        # Stage 4: download SVG files

        def download_progress(index: int, total: int, msg: str, results: dict[str, Any]) -> None:
            self.result.stages.download.message = f"Downloading {index}/{total}: {msg}"
            # if index % 10 == 0:
            self._save_progress()

            for title, _result in results.items():
                if title in self.result.files_processed:
                    item = self.result.files_processed[title]
                    if not item.steps.download.msg:  # to avoid overwriting previous messages
                        item.steps.download = StepResult(
                            result=_result.get("result", ""),
                            msg=_result.get("msg", ""),
                        )
                        if _result.get("result", "") is False:
                            item.status = "failed"
                            item.error = _result.get("msg", "")

        def download_run_after() -> None:
            download_data = self.result.stages.download.data
            self.files_dict = download_data["files_dict"]

            # clean up
            self.result.stages.download.data["results"] = {}
            self.result.stages.download.data["files"] = []

        if not self._run_stage(
            self.result.stages.download,
            step_func=lambda: download_step(
                titles=self.titles,
                output_dir=output_dir_main,
                session=self.session,
                cancel_check=lambda: self._is_cancelled(self.result.stages.download),
                overwrite_downloads=self.overwrite_downloads,
                progress_callback=download_progress,
            ),
            run_after_func=download_run_after,
        ):
            return self.result
        # ----------------------------------------------
        # Stage 5: Analyze And Fix Nested Files

        def fix_nested_progress(index: int, total: int, msg: str, results: dict[str, Any]) -> None:
            self.result.stages.nested.message = f"Analyzing {index}/{total}: {msg}"
            if index % 10 == 0:
                self._save_progress()

            for title, nested_result in results.items():
                if title in self.result.files_processed:
                    item = self.result.files_processed[title]

                    if not item.steps.nested.msg:  # to avoid overwriting previous messages
                        item.steps.nested = StepResult(
                            result=nested_result.get("result", ""),
                            msg=nested_result.get("msg", ""),
                        )
                        if nested_result.get("result", "") is False:
                            item.status = "failed"
                            item.error = nested_result.get("msg", "")

        def nested_run_after() -> None:
            nested_stage_data = self.result.stages.nested.data
            self.nested_data = nested_stage_data["data"]
            self.nested_results = nested_stage_data.get("results", {})

            # clean up
            # self.result.stages.nested.data["data"] = {}
            # self.result.stages.nested.data["results"] = {}

            return

        if not self._run_stage(
            self.result.stages.nested,
            step_func=lambda: fix_nested_step(
                self.files_dict,
                cancel_check=lambda: self._is_cancelled(self.result.stages.nested),
                progress_callback=fix_nested_progress,
            ),
            run_after_func=nested_run_after,
        ):
            return self.result
        # ----------------------------------------------
        # Stage 6: Inject translations

        def inject_run_after() -> None:
            inject_stage_data = self.result.stages.inject.data

            inject_results = inject_stage_data["results"]
            self.inject_data = inject_stage_data["data"]

            inject_files = self.inject_data.get("files", {})

            self.files_to_upload = {title: data for title, data in inject_files.items() if data.get("file_path")}

            # Update files_processed with inject results
            for title, item in self.result.files_processed.items():
                file_data = inject_results.get(title, {})

                if not file_data:
                    file_data = {"result": False, "msg": "Injection failed or skipped", "new_languages": 0}

                item.steps.inject = StepResult(
                    result=file_data.get("result"),
                    msg=file_data.get("msg", ""),
                )
                if file_data.get("result") is False:
                    item.status = "failed"
                    item.error = file_data.get("msg", "")

            # clean up
            self.result.stages.inject.data["data"] = {}
            self.result.stages.inject.data["results"] = {}

        if not self._run_stage(
            self.result.stages.inject,
            step_func=lambda: inject_step(
                self.files_dict,
                self.translations,
                self.output_dir,
                overwrite=bool(self.args.get("overwrite")),
            ),
            run_after_func=inject_run_after,
        ):
            return self.result
        # ----------------------------------------------
        # Stage 7: Upload

        def upload_progress(index: int, total: int, msg: str) -> None:
            if index % 10 == 0:
                self._save_progress()

        def upload_run_after() -> None:
            upload_result_data = self.result.stages.upload.data
            upload_result = {
                "done": upload_result_data["summary"]["uploaded"],
                "not_done": upload_result_data["summary"]["failed"],
                "no_changes": upload_result_data["summary"]["no_changes"],
                "errors": upload_result_data["errors"],
            }
            self.result.results_summary["upload_result"] = upload_result

            upload_results = upload_result_data.get("results", {})

            # Update files_processed with upload results
            for title, item in self.result.files_processed.items():
                if title in upload_results:
                    item_upload_result = upload_results[title]
                    item.steps.upload = StepResult(
                        result=item_upload_result.get("result", ""),
                        msg=item_upload_result.get("msg", ""),
                    )

                    if item_upload_result.get("result", "") is True:
                        item.status = "completed"
                    elif item_upload_result.get("result", "") is False:
                        item.status = "failed"
                        item.error = item_upload_result.get("msg", "")
                    elif item_upload_result.get("result", "") is None:
                        # Skipped or no changes
                        item.status = "completed"

                if item.status == "pending":
                    item.status = "completed"

        if not bool(self.args.get("upload")):
            upload_result = {"done": 0, "not_done": len(self.files_to_upload), "skipped": True}
            self.result.results_summary["upload_result"] = upload_result
            self.log_upload_error("Upload disabled", None, "Skipped")

        elif not self.site:
            upload_result = {"done": 0, "not_done": len(self.files_to_upload), "failed": True}
            self.result.results_summary["upload_result"] = upload_result
            self.log_upload_error("Authentication failed", False, "Failed")
        else:
            if not self._run_stage(
                self.result.stages.upload,
                step_func=lambda: upload_step(
                    self.files_to_upload,
                    self.main_title,
                    self.site,
                    cancel_check=lambda: self._is_cancelled(self.result.stages.upload),
                    progress_callback=upload_progress,
                    upload_limit=self.upload_limit,
                ),
                run_after_func=upload_run_after,
            ):
                return self.result

        # ----------------------------------------------
        # Stage 8: save stats and mark done
        stats_data = {
            "main_title": self.main_title,
            "translations": self.translations,
            "titles": self.titles,
            "files": self.files_dict,
            "files_dict": self.files_dict,
            "nested_task_result": self.nested_data,
            "injects_result": self.inject_data,
        }

        self._save_files_stats(stats_data)

        # Compile final results for database
        self.result.results_summary.update(
            {
                "total_files": len(self.files_dict),
                "files_to_upload_count": len(self.files_to_upload),
                "no_file_path": len(self.files_dict) - len(self.files_to_upload),
                "injects_result": {
                    "nested_files": self.inject_data.get("nested_files", 0),
                    "success": self.inject_data.get("success", 0),
                    "failed": self.inject_data.get("failed", 0),
                },
                "new_translations_count": len(self.translations.get("new", {})),
                "main_title": self.main_title,
            }
        )

        return self.result


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
