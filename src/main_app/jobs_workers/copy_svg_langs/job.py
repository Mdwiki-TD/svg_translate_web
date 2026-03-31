"""Processor for copying SVG languages (translations) between versions."""

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
from .steps.download import download_step
from .steps.extract_text import extract_text_step
from .steps.extract_titles import extract_titles_step
from .steps.extract_translations import extract_translations_step
from .steps.fix_nested import fix_nested_step
from .steps.inject import inject_step
from .steps.upload import upload_step
from .utils import json_save, make_results_summary

logger = logging.getLogger(__name__)


@dataclass
class CopySvgLangsProcessor:
    """
    Orchestrates the pipeline for copying SVG translations.
    """

    job_id: str | int
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
        return out

    def _save_progress(self) -> None:
        try:
            jobs_service.save_job_result_by_name(self.result_file, self.result)
        except Exception:
            logger.exception(f"Job {self.job_id}: Failed to save progress")

    def _is_cancelled(self, stage_name: str | None = None) -> bool:
        cancelled = False
        if self.cancel_event and self.cancel_event.is_set():
            cancelled = True
        elif jobs_service.is_job_cancelled(self.job_id, job_type="copy_svg_langs"):
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

        # 1. Extract Text
        if not self._run_stage("text", extract_text_step, self.title):
            return self.result
        text = self.result["stages"]["text"]["data"]["text"]

        # 2. Extract Titles
        if not self._run_stage(
            "titles",
            extract_titles_step,
            text,
            manual_main_title=self.args.manual_main_title,
            titles_limit=self.args.titles_limit,
        ):
            return self.result
        titles_data = self.result["stages"]["titles"]["data"]
        main_title = titles_data["main_title"]
        titles = titles_data["titles"]

        # 3. Extract Translations
        output_dir_main = self.output_dir / "files"
        output_dir_main.mkdir(parents=True, exist_ok=True)
        if not self._run_stage("translations", extract_translations_step, main_title, output_dir_main):
            return self.result
        translations = self.result["stages"]["translations"]["data"]["translations"]

        # 4. Download
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
        files = self.result["stages"]["download"]["data"]["files"]

        # 5. Fix Nested
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
        nested_data = self.result["stages"]["nested"]["data"]["data"]

        # 6. Inject
        if not self._run_stage(
            "inject",
            inject_step,
            files,
            translations,
            self.output_dir,
            overwrite=self.args.overwrite,
        ):
            return self.result
        inject_data = self.result["stages"]["inject"]["data"]["data"]
        files_to_upload = self.result["stages"]["inject"]["data"]["files_to_upload"]

        # 7. Upload
        if not self.args.upload:
            self.result["stages"]["upload"]["status"] = "Skipped"
            self.result["stages"]["upload"]["message"] = "Upload disabled"
            upload_result = {"done": 0, "not_done": len(files_to_upload), "skipped": True}
        elif not self.site:
            self.result["stages"]["upload"]["status"] = "Failed"
            self.result["stages"]["upload"]["message"] = "Authentication failed"
            upload_result = {"done": 0, "not_done": len(files_to_upload), "failed": True}
        else:

            def upload_progress(index: int, total: int, msg: str) -> None:
                self.result["stages"]["upload"]["message"] = f"Uploading {index}/{total}: {msg}"
                if index % 10 == 0:
                    self._save_progress()

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

        # Save stats file
        stats_data = {
            "main_title": main_title,
            "translations": translations,
            "titles": titles,
            "files": files,
            "nested_task_result": nested_data,
            "injects_result": inject_data,
        }
        json_save(self.output_dir / "files_stats.json", stats_data)

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
