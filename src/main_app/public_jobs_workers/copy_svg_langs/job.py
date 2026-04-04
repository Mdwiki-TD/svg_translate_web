"""
Processor for copy_svg_langs
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import mwclient
import requests

from ...api_services.clients import create_commons_session, get_user_site
from ...config import settings
from ...services import jobs_service
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


@dataclass
class CopySvgLangsProcessor:
    """
    Orchestrates the pipeline for copying SVG translations.
    """

    task_id: str | int
    title: str
    args: Any
    user: dict[str, Any] | None
    result: dict[str, Any]
    result_file: str
    cancel_event: threading.Event | None = None

    site: mwclient.Site | None = field(init=False, default=None)
    session: requests.Session | None = field(init=False, default=None)
    output_dir: Path = field(init=False)

    files: list[str] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.output_dir = self._compute_output_dir(self.title)

    def _compute_output_dir(self, title: str) -> Path:
        name = Path(title).name
        slug = re.sub(r"[^A-Za-z0-9._\- ]+", "_", str(name)).strip("._") or "untitled"
        slug = slug.replace(" ", "_").lower()
        out = Path(settings.paths.svg_data) / slug
        out.mkdir(parents=True, exist_ok=True)

        return out

    def _save_progress(self) -> None:
        try:
            jobs_service.save_job_result_by_name(self.result_file, self.result)
        except Exception:
            logger.exception(f"Job {self.task_id}: Failed to save progress")

    def _is_cancelled(self, stage_name: str | None = None) -> bool:
        cancelled = False
        if self.cancel_event and self.cancel_event.is_set():
            cancelled = True
        elif jobs_service.is_job_cancelled(self.task_id, job_type="copy_svg_langs"):
            cancelled = True

        if cancelled:
            self.result["status"] = "cancelled"
            if self.result.get("cancelled_at") is None:
                self.result["cancelled_at"] = datetime.now().isoformat()
            if stage_name and stage_name in self.result.get("stages", {}):
                self.result["stages"][stage_name]["status"] = "Cancelled"
            return True
        return False

    def run(self) -> dict[str, Any]:
        """Execute the full pipeline."""
        self.result["status"] = "running"
        self._save_progress()

        self.session = create_commons_session(settings.oauth.user_agent)
        self.site = get_user_site(self.user)

        # ----------------------------------------------
        # Stage 1: Extract Text
        def text_run_after() -> None:
            self.text = self.result["stages"]["text"]["data"]["text"]
            # clean up
            self.result["stages"]["text"]["data"]["text"] = ""

        if not self._run_stage(
            "text",
            extract_text_step,
            text_run_after,
            self.title,
        ):
            return self.result

        # ----------------------------------------------
        # Stage 2: Extract Titles
        def titles_run_after() -> None:
            titles_data = self.result["stages"]["titles"]["data"]
            self.main_title = titles_data["main_title"]
            self.titles = list(titles_data["titles"])

            # clean up
            self.result["stages"]["titles"]["data"]["titles"] = []

        if not self._run_stage(
            "titles",
            extract_titles_step,
            titles_run_after,
            self.text,
            manual_main_title=self.args.get("manual_main_title"),
        ):
            return self.result

        # Initialize files_processed

        for title in self.titles:
            self.result["files_processed"].append(
                {
                    "title": title,
                    "status": "pending",
                    "error": None,
                    "steps": {
                        "download": {"result": None, "msg": ""},
                        "nested": {"result": None, "msg": ""},
                        "inject": {"result": None, "msg": ""},
                        "upload": {"result": None, "msg": ""},
                    }
                }
            )

        # ----------------------------------------------
        # Stage 3: Extract Translations
        output_dir_main = self.output_dir / "files"
        output_dir_main.mkdir(parents=True, exist_ok=True)

        def translations_run_after() -> None:
            data = self.result["stages"]["translations"]["data"]
            self.translations = data["translations"]
            # self.result["stages"]["translations"]["message"] = data["message"]

        if not self._run_stage(
            "translations",
            extract_translations_step,
            translations_run_after,
            self.main_title,
            output_dir_main,
        ):
            return self.result
        # ----------------------------------------------
        # Stage 4: download SVG files

        def download_progress(index: int, total: int, msg: str) -> None:
            self.result["stages"]["download"]["message"] = f"Downloading {index}/{total}: {msg}"
            if index % 10 == 0:
                self._save_progress()

        def download_run_after() -> None:
            download_data = self.result["stages"]["download"]["data"]
            self.files = download_data["files"]
            download_results = download_data.get("results", {})

            # Update files_processed with download results
            for item in self.result["files_processed"]:
                title = item["title"]
                if title in download_results:
                    item["steps"]["download"] = download_results[title]
                    if download_results[title].get("result"):
                        item["file_path"] = download_results[title].get("path")

                    if download_results[title]["result"] is False:
                        item["status"] = "failed"
                        item["error"] = download_results[title]["msg"]

            # clean up
            self.result["stages"]["download"]["data"]["results"] = {}
            self.result["stages"]["download"]["data"]["files"] = []

        if not self._run_stage(
            "download",
            download_step,
            download_run_after,
            self.titles,
            output_dir_main,
            session=self.session,
            cancel_check=lambda: self._is_cancelled("download"),
            progress_callback=download_progress,
        ):
            return self.result
        # ----------------------------------------------
        # Stage 5: Analyze And Fix Nested Files

        def fix_nested_progress(index: int, total: int, msg: str) -> None:
            self.result["stages"]["nested"]["message"] = f"Analyzing {index}/{total}: {msg}"
            if index % 10 == 0:
                self._save_progress()

        def nested_run_after() -> None:
            nested_stage_data = self.result["stages"]["nested"]["data"]
            self.nested_data = nested_stage_data["data"]
            self.nested_results = nested_stage_data.get("results", {})

            # clean up
            self.result["stages"]["nested"]["data"]["data"] = {}
            self.result["stages"]["nested"]["data"]["results"] = {}

            # Update files_processed with nested results
            for item in self.result["files_processed"]:
                # Need to find the file path associated with this title
                # download_one_file saves to output_dir_main / title
                file_path = str(output_dir_main / item["title"])
                if file_path in self.nested_results:
                    item["steps"]["nested"] = self.nested_results[file_path]
                    if self.nested_results[file_path]["result"] is False:
                        # We don't necessarily mark the whole file as failed if nested fix fails
                        # as it might still be injectable.
                        pass

        if not self._run_stage(
            "nested",
            fix_nested_step,
            nested_run_after,
            self.files,
            cancel_check=lambda: self._is_cancelled("nested"),
            progress_callback=fix_nested_progress,
        ):
            return self.result
        # ----------------------------------------------
        # Stage 6: Inject translations

        def inject_run_after() -> None:
            inject_stage_data = self.result["stages"]["inject"]["data"]
            self.inject_data = inject_stage_data["data"]
            self.files_to_upload = inject_stage_data["files_to_upload"]

            inject_results = inject_stage_data.get("results", {})

            # Update files_processed with inject results
            for item in self.result["files_processed"]:
                file_path = str(output_dir_main / item["title"])
                if file_path in inject_results:
                    item["steps"]["inject"] = inject_results[file_path]
                    if inject_results[file_path]["result"] is False:
                        item["status"] = "failed"
                        item["error"] = inject_results[file_path]["msg"]

            # clean up
            self.result["stages"]["inject"]["data"]["data"] = {}
            self.result["stages"]["inject"]["data"]["results"] = {}

        if not self._run_stage(
            "inject",
            inject_step,
            inject_run_after,
            self.files,
            self.translations,
            self.output_dir,
            overwrite=bool(self.args.get("overwrite")),
        ):
            return self.result
        # ----------------------------------------------
        # Stage 7: Upload

        def upload_progress(index: int, total: int, msg: str) -> None:
            if index % 10 == 0:
                self._save_progress()

        def upload_run_after() -> None:
            upload_result_data = self.result["stages"]["upload"]["data"]
            upload_result = {
                "done": upload_result_data["summary"]["uploaded"],
                "not_done": upload_result_data["summary"]["failed"],
                "no_changes": upload_result_data["summary"]["no_changes"],
                "errors": upload_result_data["errors"],
            }
            self.result["results_summary"]["upload_result"] = upload_result

            upload_results = upload_result_data.get("results", {})

            # Update files_processed with upload results
            for item in self.result["files_processed"]:
                # upload_step results are keyed by filename (title)
                title = item["title"]
                if title in upload_results:
                    item["steps"]["upload"] = upload_results[title]
                    if upload_results[title]["result"] is True:
                        item["status"] = "completed"
                    elif upload_results[title]["result"] is False:
                        item["status"] = "failed"
                        item["error"] = upload_results[title]["msg"]
                    elif upload_results[title]["result"] is None:
                        # Skipped or no changes
                        item["status"] = "completed"

                if item["status"] == "pending":
                    item["status"] = "completed"

        if not bool(self.args.get("upload")):
            upload_result = {"done": 0, "not_done": len(self.files_to_upload), "skipped": True}
            self.result["results_summary"]["upload_result"] = upload_result
            self.log_upload_error("Upload disabled", None, "Skipped")

        elif not self.site:
            upload_result = {"done": 0, "not_done": len(self.files_to_upload), "failed": True}
            self.result["results_summary"]["upload_result"] = upload_result
            self.log_upload_error("Authentication failed", False, "Failed")
        else:
            if not self._run_stage(
                "upload",
                upload_step,
                upload_run_after,
                self.files_to_upload,
                self.main_title,
                self.site,
                cancel_check=lambda: self._is_cancelled("upload"),
                progress_callback=upload_progress,
            ):
                return self.result

        # ----------------------------------------------
        # Stage 8: save stats and mark done
        stats_data = {
            "main_title": self.main_title,
            "translations": self.translations,
            "titles": self.titles,
            "files": self.files,
            "nested_task_result": self.nested_data,
            "injects_result": self.inject_data,
        }

        self._save_files_stats(stats_data)

        # Finalize
        self.result["status"] = "completed"
        self.result["completed_at"] = datetime.now().isoformat()

        # Compile final results for database
        self.result["results_summary"] = {
            "total_files": len(self.files),
            "files_to_upload_count": len(self.files_to_upload),
            "no_file_path": len(self.files) - len(self.files_to_upload),
            "injects_result": {
                "nested_files": self.inject_data.get("nested_files", 0),
                "success": self.inject_data.get("success", 0),
                "failed": self.inject_data.get("failed", 0),
            },
            "new_translations_count": len(self.translations.get("new", {})),
            "main_title": self.main_title,
        }

        self._save_progress()
        return self.result

    def log_upload_error(self, _msg, result, status):
        self.result["stages"]["upload"]["status"] = status
        self.result["stages"]["upload"]["message"] = _msg

        for item in self.result["files_processed"]:
            if item["status"] != "failed":
                item["steps"]["upload"] = {"result": result, "msg": _msg}
                item["status"] = status
                item["error"] = _msg

    def _save_files_stats(self, stats_data):
        files_stats_path = self.output_dir / "files_stats.json"
        try:
            with open(files_stats_path, "w", encoding="utf-8") as f:
                json.dump(stats_data, f, indent=4, ensure_ascii=False)

        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Error saving json: {e}, path: {str(files_stats_path)}")
        except Exception:
            logger.exception(f"Unexpected error saving json, path: {str(files_stats_path)}")

    def _run_stage(
        self,
        stage_name: str,
        step_func: Any,
        run_after_func: Any | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Run a single stage and update result."""
        if self._is_cancelled(stage_name):
            return False

        stage = self.result["stages"][stage_name]
        stage["status"] = "Running"
        self._save_progress()

        try:
            step_result = step_func(*args, **kwargs)
            stage["data"] = step_result
            if step_result.get("message"):
                self.result["stages"][stage_name]["message"] = step_result["message"]

            if step_result.get("success"):
                stage["status"] = "Completed"
                if "summary" in step_result and "message" not in stage:
                    summary = step_result["summary"]
                    if isinstance(summary, dict):
                        stage["message"] = ", ".join(f"{k}: {v}" for k, v in summary.items())

                if run_after_func:
                    run_after_func()
                return True
            else:
                stage["status"] = "Failed"
                stage["message"] = step_result.get("error", "Unknown error")
                self.result["status"] = "failed"
                return False

        except Exception as e:
            logger.exception(f"Error in stage {stage_name}")
            stage["status"] = "Failed"
            stage["message"] = str(e)
            self.result["status"] = "failed"
            return False
