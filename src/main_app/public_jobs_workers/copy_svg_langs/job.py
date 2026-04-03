"""
Processor for copy_svg_langs
"""

from __future__ import annotations

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
from ..utils import json_save, make_results_summary
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

    def __post_init__(self) -> None:
        self.output_dir = self._compute_output_dir(self.title)

    def _compute_output_dir(self, title: str) -> Path:
        name = Path(title).name
        slug = re.sub(r"[^A-Za-z0-9._\- ]+", "_", str(name)).strip("._") or "untitled"
        slug = slug.replace(" ", "_").lower()
        out = Path(settings.paths.svg_data) / slug
        out.mkdir(parents=True, exist_ok=True)

        # log title to out/title.txt
        try:
            with open(out / "title.txt", "w", encoding="utf-8") as f:
                f.write(name)
        except Exception as e:
            logger.error(f"Failed to write title to {out / 'title.txt'}: {e}")

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
        if not self._run_stage("text", extract_text_step, self.title):
            return self.result
        text = self.result["stages"]["text"]["data"]["text"]

        # clean up
        self.result["stages"]["text"]["data"]["text"] = ""
        # ----------------------------------------------
        # Stage 2: Extract Titles
        if not self._run_stage(
            "titles",
            extract_titles_step,
            text,
            manual_main_title=self.args.get("manual_main_title"),
        ):
            return self.result

        titles_data = self.result["stages"]["titles"]["data"]
        main_title = titles_data["main_title"]
        titles = list(titles_data["titles"])
        self.result["stages"]["titles"]["message"] = titles_data["message"]

        # clean up
        self.result["stages"]["titles"]["data"]["titles"] = []

        # Initialize files_processed
        self.result["files_processed"] = []
        for title in titles:
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
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

        # ----------------------------------------------
        # Stage 3: Extract Translations
        output_dir_main = self.output_dir / "files"
        output_dir_main.mkdir(parents=True, exist_ok=True)
        if not self._run_stage("translations", extract_translations_step, main_title, output_dir_main):
            return self.result
        translations = self.result["stages"]["translations"]["data"]["translations"]
        self.result["stages"]["translations"]["message"] = titles_data["message"]

        # ----------------------------------------------
        # Stage 4: download SVG files
        def download_progress(index: int, total: int, msg: str) -> None:
            self.result["stages"]["download"]["message"] = f"Downloading {index}/{total}: {msg}"
            if index % 10 == 0:
                self._save_progress()

        if not self._run_stage(
            "download",
            download_step,
            titles,
            output_dir_main,
            session=self.session,
            cancel_check=lambda: self._is_cancelled("download"),
            progress_callback=download_progress,
        ):
            return self.result
        download_data = self.result["stages"]["download"]["data"]
        files = download_data["files"]
        download_results = download_data.get("results", {})

        # Update files_processed with download results
        for item in self.result["files_processed"]:
            title = item["title"]
            if title in download_results:
                item["steps"]["download"] = download_results[title]
                if download_results[title]["result"] is False:
                    item["status"] = "failed"
                    item["error"] = download_results[title]["msg"]

        # ----------------------------------------------
        # Stage 5: Analyze And Fix Nested Files
        def fix_nested_progress(index: int, total: int, msg: str) -> None:
            self.result["stages"]["nested"]["message"] = f"Analyzing {index}/{total}: {msg}"
            if index % 10 == 0:
                self._save_progress()

        if not self._run_stage(
            "nested",
            fix_nested_step,
            files,
            cancel_check=lambda: self._is_cancelled("nested"),
            progress_callback=fix_nested_progress,
        ):
            return self.result
        nested_stage_data = self.result["stages"]["nested"]["data"]
        nested_data = nested_stage_data["data"]
        nested_results = nested_stage_data.get("results", {})

        # clean up
        self.result["stages"]["nested"]["data"]["data"] = {}
        self.result["stages"]["nested"]["data"]["results"] = {}

        # Update files_processed with nested results
        for item in self.result["files_processed"]:
            # Need to find the file path associated with this title
            # download_one_file saves to output_dir_main / title
            file_path = str(output_dir_main / item["title"])
            if file_path in nested_results:
                item["steps"]["nested"] = nested_results[file_path]
                if nested_results[file_path]["result"] is False:
                    # We don't necessarily mark the whole file as failed if nested fix fails
                    # as it might still be injectable.
                    pass

        # ----------------------------------------------
        # Stage 6: Inject translations
        if not self._run_stage(
            "inject",
            inject_step,
            files,
            translations,
            self.output_dir,
            overwrite=bool(self.args.get("overwrite")),
        ):
            return self.result

        inject_stage_data = self.result["stages"]["inject"]["data"]
        inject_data = inject_stage_data["data"]
        files_to_upload = inject_stage_data["files_to_upload"]
        inject_results = inject_stage_data.get("results", {})

        # clean up
        self.result["stages"]["inject"]["data"]["data"] = {}

        # Update files_processed with inject results
        for item in self.result["files_processed"]:
            file_path = str(output_dir_main / item["title"])
            if file_path in inject_results:
                item["steps"]["inject"] = inject_results[file_path]
                if inject_results[file_path]["result"] is False:
                    item["status"] = "failed"
                    item["error"] = inject_results[file_path]["msg"]

        # ----------------------------------------------
        # Stage 7: Upload
        def upload_progress(index: int, total: int, msg: str) -> None:
            if index % 10 == 0:
                self._save_progress()

        if not bool(self.args.get("upload")):
            self.result["stages"]["upload"]["status"] = "Skipped"
            self.result["stages"]["upload"]["message"] = "Upload disabled"
            upload_result = {"done": 0, "not_done": len(files_to_upload), "skipped": True}
            for item in self.result["files_processed"]:
                if item["status"] != "failed":
                    item["steps"]["upload"] = {"result": None, "msg": "Upload disabled"}
                    item["status"] = "Skipped"

        elif not self.site:
            self.result["stages"]["upload"]["status"] = "Failed"
            self.result["stages"]["upload"]["message"] = "Authentication failed"
            upload_result = {"done": 0, "not_done": len(files_to_upload), "failed": True}
            for item in self.result["files_processed"]:
                if item["status"] != "failed":
                    item["steps"]["upload"] = {"result": False, "msg": "Authentication failed"}
                    item["status"] = "failed"
                    item["error"] = "Authentication failed"
        else:

            if not self._run_stage(
                "upload",
                upload_step,
                files_to_upload,
                main_title,
                self.site,
                cancel_check=lambda: self._is_cancelled("upload"),
                progress_callback=upload_progress,
            ):
                return self.result
            upload_result_data = self.result["stages"]["upload"]["data"]
            upload_result = {
                "done": upload_result_data["summary"]["uploaded"],
                "not_done": upload_result_data["summary"]["failed"],
                "no_changes": upload_result_data["summary"]["no_changes"],
                "errors": upload_result_data["errors"],
            }
            upload_results = upload_result_data.get("results", {})

            # Total Files: 425, uploaded 425, no changes: 0, not uploaded: 0
            self.result["stages"]["upload"]["message"] = f"Uploaded {len(upload_result["done"])}/{len(files_to_upload)}, No Changes {upload_result['no_changes']}, Errors {upload_result['errors']}"

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

            # Final check for files that didn't reach upload but didn't fail
            for item in self.result["files_processed"]:
                if item["status"] == "pending":
                    item["status"] = "completed"

        # ----------------------------------------------
        # Stage 8: save stats and mark done
        stats_data = {
            "main_title": main_title,
            "translations": translations,
            "titles": titles,
            "files": files,
            "nested_task_result": nested_data,
            "injects_result": inject_data,
        }
        json_save(self.output_dir / "files_stats.json", stats_data)

        # Finalize
        self.result["status"] = "completed"
        self.result["completed_at"] = datetime.now().isoformat()

        # Compile final results for database
        results_summary = make_results_summary(
            len(files),
            len(files_to_upload),
            len(files) - len(files_to_upload),
            inject_data,
            translations,
            main_title,
            upload_result,
        )
        self.result["results_summary"] = results_summary

        self._save_progress()
        return self.result

    def _run_stage(self, stage_name: str, step_func: Any, *args: Any, **kwargs: Any) -> bool:
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
                    s = step_result["summary"]
                    if isinstance(s, dict):
                        stage["message"] = ", ".join(f"{k}: {v}" for k, v in s.items())
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
