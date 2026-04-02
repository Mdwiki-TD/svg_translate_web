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
from typing import Any, Dict

import mwclient
import requests

from ...api_services.clients import create_commons_session, get_user_site
from ...config import settings
from ...db.copy_svg_langs_db import TaskStorePyMysql
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

        # log title to out/title.txt
        try:
            with open(out / "title.txt", "w", encoding="utf-8") as f:
                f.write(name)
        except Exception as e:
            logger.error(f"Failed to write title to {out / 'title.txt'}: {e}")

        return out

    def fail_task(
        self,
        stage_name: str,
        msg: str,
    ) -> None:
        """
        Mark the task as failed in the provided TaskStore and log an optional error message.
        """
        self.result["stages"]["initialize"]["status"] = "Completed"
        self.store.update_stage(self.task_id, "initialize", self.result["stages"]["initialize"])
        self.store.update_status(self.task_id, "Failed")
        logger.error(msg)
        return

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
            self.result["stages"]["initialize"]["status"] = "Completed"

            if stage_name and stage_name in self.result.get("stages", {}):
                stage_state = self.result["stages"].get(stage_name)
                # if stage_state and stage_state.get("status") == "Running":
                stage_state["status"] = "Cancelled"
                self.push_stage(stage_name, stage_state)

            self.push_stage("initialize")
            self.store.update_status(self.task_id, "Cancelled")
            logger.debug(f"Task: {self.task_id} Cancelled.")
            return True
        return False

    def push_stage(self, stage_name: str, stage_state: Dict[str, Any] | None = None) -> None:
        """
        Persist the current state of a workflow stage to the task store.

        If `stage_state` is omitted, the function uses the stage state from the surrounding `self.result["stages"]`.
        Parameters:
            stage_name (str): Name of the stage to persist.
            stage_state (dict | None): Explicit stage state to persist; when `None`, use the current state from `self.result["stages"]`.
        """
        state = stage_state if stage_state is not None else self.result["stages"][stage_name]
        self.store.update_stage(self.task_id, stage_name, state)

    def run(self) -> dict[str, Any]:
        """Execute the full pipeline."""
        self.result["status"] = "running"
        self._save_progress()

        self.session = create_commons_session(settings.oauth.user_agent)
        self.site = get_user_site(self.user)

        task_snapshot: Dict[str, Any] = {
            "title": self.title,
        }

        self.store = TaskStorePyMysql(settings.database_data)

        self.store.update_data(self.task_id, task_snapshot)

        if self.cancel_event is not None and self.cancel_event.is_set():
            if self._is_cancelled("initialize"):
                return None

        self.store.update_status(self.task_id, "Running")

        # -------------------------------------------
        # Stage 1: extract text
        text, self.result["stages"]["text"] = extract_text_step(self.result["stages"]["text"], self.title)
        self.push_stage("text")
        if self._is_cancelled("text"):
            return None
        if not text:
            return self.fail_task("text", "No text extracted")

        # ----------------------------------------------
        # Stage 2: Extract Titles
        titles_result, self.result["stages"]["titles"] = extract_titles_step(
            self.result["stages"]["titles"],
            text,
            manual_main_title=self.args.get("manual_main_title"),
        )

        self.push_stage("titles")
        if self._is_cancelled("titles"):
            return None

        main_title, titles = titles_result["main_title"], titles_result["titles"]

        if not main_title:
            return self.fail_task("titles", "No main title found")

        value = f"File:{main_title}" if not main_title.lower().startswith("file:") else main_title
        self.store.update_task_one_column(self.task_id, "main_file", value)

        if not titles:
            return self.fail_task("titles", "No titles found")

        # ----------------------------------------------
        # Stage 3: Extract Translations
        output_dir_main = self.output_dir / "files"
        output_dir_main.mkdir(parents=True, exist_ok=True)

        translations, self.result["stages"]["translations"] = extract_translations_step(
            self.result["stages"]["translations"], main_title, output_dir_main
        )
        self.push_stage("translations")
        if self._is_cancelled("translations"):
            return None

        if not translations:
            return self.fail_task("translations", "No translations available")

        # ----------------------------------------------
        # Stage 4: download SVG files
        def download_progress(index: int, total: int, msg: str) -> None:
            self.result["stages"]["download"]["message"] = f"Downloading {index}/{total}: {msg}"
            if index % 10 == 0:
                self._save_progress()

        files, self.result["stages"]["download"], not_done_list = download_step(
            self.task_id,
            stages=self.result["stages"]["download"],
            output_dir_main=output_dir_main,
            titles=titles,
            store=self.store,
            _is_cancelled=self._is_cancelled,
        )
        if not_done_list:
            task_snapshot["not_done_list"] = not_done_list
            self.store.update_data(self.task_id, task_snapshot)

        self.push_stage("download")
        if self._is_cancelled("download"):
            return None

        if not files:
            return self.fail_task("download", "No files downloaded")

        # ----------------------------------------------
        # Stage 5: Analyze And Fix Nested Files
        def fix_nested_progress(index: int, total: int, msg: str) -> None:
            self.result["stages"]["nested"]["message"] = f"Analyzing {index}/{total}: {msg}"
            if index % 10 == 0:
                self._save_progress()

        nested_data, self.result["stages"]["nested"] = fix_nested_step(
            self.result["stages"]["nested"],
            files,
        )
        self.push_stage("nested")
        if self._is_cancelled("nested"):
            return None

        # ----------------------------------------------
        # Stage 6: Inject translations
        inject_data, self.result["stages"]["inject"] = inject_step(
            self.result["stages"]["inject"],
            files,
            translations,
            self.output_dir,
            overwrite=bool(self.args.get("overwrite")),
        )
        self.push_stage("inject")
        if self._is_cancelled("inject"):
            return None

        if not inject_data:
            return self.fail_task("inject", "Injection result error")

        if inject_data.get("success", 0) == 0 and inject_data.get("saved_done", 0) == 0:
            return self.fail_task("inject", "Injection saved 0 files")

        inject_files = {x: v for x, v in inject_data.get("files", {}).items() if x != main_title}

        # ----------------------------------------------
        # Stage 7: Upload
        def upload_progress(index: int, total: int, msg: str) -> None:
            self.result["stages"]["upload"]["message"] = f"Uploading {index}/{total}: {msg}"
            if index % 10 == 0:
                self._save_progress()

        files_to_upload = {x: v for x, v in inject_files.items() if v.get("file_path")}

        upload_result, self.result["stages"]["upload"] = upload_step(
            self.result["stages"]["upload"],
            files_to_upload,
            main_title,
            do_upload=bool(self.args.get("upload")),
            user=self.user,
            store=self.store,
            task_id=self.task_id,
            _is_cancelled=self._is_cancelled,
        )

        self.push_stage("upload")
        if self._is_cancelled("upload"):
            return None

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
            len(inject_files) - len(files_to_upload),
            inject_data,
            translations,
            main_title,
            upload_result,
        )

        self.store.update_results(self.task_id, results_summary)

        final_status = (
            "Failed" if any(s.get("status") == "Failed" for s in self.result["stages"].values()) else "Completed"
        )
        self.result["stages"]["initialize"]["status"] = "Completed"
        self.push_stage("initialize")

        if self._is_cancelled("initialize"):
            return None

        self.store.update_status(self.task_id, final_status)

        self._save_progress()
        return self.result

    def _run_stage(self, stage_name: str, step_func: Any, *args: Any, **kwargs: Any) -> bool:
        """Run a single stage and update result."""
        if self._is_cancelled(stage_name):
            return False

        stage = self.result["stages"][stage_name]
        stage["status"] = "Running"
        self._save_progress()
