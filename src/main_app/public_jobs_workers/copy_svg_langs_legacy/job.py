"""
Processor for copy_svg_langs
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import mwclient
import requests

from ...config import settings
from ...db.copy_svg_langs_db import TaskStorePyMysql
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


def fail_task(
    store: TaskStorePyMysql,
    task_id: str,
    stages: Dict[str, Dict[str, Any]],
    msg: str | None = None,
) -> None:
    """
    Mark the task as failed in the provided TaskStore and log an optional error message.

    This sets the `"initialize"` stage status to `"Completed"`, persists the updated snapshot via the store, and marks the task status as `"Failed"`.

    Parameters:
        snapshot (Dict[str, Any]): Current task snapshot; must contain a `"stages"` mapping.
        msg (str | None): Optional error message to log.
    """
    stages["initialize"]["status"] = "Completed"
    store.update_stage(task_id, "initialize", stages["initialize"])
    store.update_status(task_id, "Failed")
    if msg:
        logger.error(msg)
    return


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
        # ---
        # log title to out/title.txt
        try:
            with open(out / "title.txt", "w", encoding="utf-8") as f:
                f.write(name)
        except Exception as e:
            logger.error(f"Failed to write title to {out / 'title.txt'}: {e}")
        # ---
        return out

    def _is_cancelled(self, stage_name: str | None = None) -> bool:
        cancelled = False
        if self.cancel_event and self.cancel_event.is_set():
            cancelled = True

        if cancelled:
            self.result["status"] = "cancelled"
            self.result["stages"]["initialize"]["status"] = "Completed"
            if stage_name:
                stage_state = self.result["stages"].get(stage_name)
                if stage_state and stage_state.get("status") == "Running":
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
        task_snapshot: Dict[str, Any] = {
            "title": self.title,
        }

        self.store = TaskStorePyMysql(settings.database_data)

        self.store.update_data(self.task_id, task_snapshot)

        if self.cancel_event is not None and self.cancel_event.is_set():
            if self._is_cancelled("initialize"):
                return None

        self.store.update_status(self.task_id, "Running")

        # ----------------------------------------------
        # Stage 1: extract text
        text, self.result["stages"]["text"] = extract_text_step(self.result["stages"]["text"], self.title)
        self.push_stage("text")
        if self._is_cancelled("text"):
            return None
        if not text:
            return fail_task(self.store, self.task_id, self.result["stages"], "No text extracted")

        # ----------------------------------------------
        # Stage 2: extract titles
        titles_result, self.result["stages"]["titles"] = extract_titles_step(
            self.result["stages"]["titles"],
            text,
            self.args.manual_main_title,
            titles_limit=self.args.titles_limit,
        )

        self.push_stage("titles")
        if self._is_cancelled("titles"):
            return None

        main_title, titles = titles_result["main_title"], titles_result["titles"]

        if not main_title:
            return fail_task(self.store, self.task_id, self.result["stages"], "No main title found")

        value = f"File:{main_title}" if not main_title.lower().startswith("file:") else main_title
        self.store.update_task_one_column(self.task_id, "main_file", value)

        if not titles:
            return fail_task(self.store, self.task_id, self.result["stages"], "No titles found")

        # ----------------------------------------------
        # Stage 3: get translations
        output_dir_main = self.output_dir / "files"
        output_dir_main.mkdir(parents=True, exist_ok=True)

        translations, self.result["stages"]["translations"] = extract_translations_step(
            self.result["stages"]["translations"], main_title, output_dir_main
        )
        self.push_stage("translations")
        if self._is_cancelled("translations"):
            return None

        if not translations:
            return fail_task(self.store, self.task_id, self.result["stages"], "No translations available")

        # ----------------------------------------------
        # Stage 4: download SVG files
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
            return fail_task(self.store, self.task_id, self.result["stages"], "No files downloaded")

        # ----------------------------------------------
        # Stage 5: analyze nested files
        nested_data, self.result["stages"]["nested"] = fix_nested_step(
            self.result["stages"]["nested"],
            files,
        )
        self.push_stage("nested")
        if self._is_cancelled("nested"):
            return None

        # ----------------------------------------------
        # Stage 6: inject translations
        inject_data, self.result["stages"]["inject"] = inject_step(
            self.result["stages"]["inject"],
            files,
            translations,
            output_dir=self.output_dir,
            overwrite=self.args.overwrite,
        )
        self.push_stage("inject")
        if self._is_cancelled("inject"):
            return None

        if not inject_data:
            return fail_task(self.store, self.task_id, self.result["stages"], "Injection result error")

        if inject_data.get("success", 0) == 0 and inject_data.get("saved_done", 0) == 0:
            return fail_task(self.store, self.task_id, self.result["stages"], "Injection saved 0 files")

        inject_files = {x: v for x, v in inject_data.get("files", {}).items() if x != main_title}

        # ----------------------------------------------
        # Stage 7: upload results
        files_to_upload = {x: v for x, v in inject_files.items() if v.get("file_path")}

        no_file_path = len(inject_files) - len(files_to_upload)

        upload_result, self.result["stages"]["upload"] = upload_step(
            self.result["stages"]["upload"],
            files_to_upload,
            main_title,
            do_upload=self.args.upload,
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

        results = make_results_summary(
            len(files), len(files_to_upload), no_file_path, inject_data, translations, main_title, upload_result
        )

        self.store.update_results(self.task_id, results)

        final_status = (
            "Failed" if any(s.get("status") == "Failed" for s in self.result["stages"].values()) else "Completed"
        )
        self.result["stages"]["initialize"]["status"] = "Completed"
        self.push_stage("initialize")

        if self._is_cancelled("initialize"):
            return None

        self.store.update_status(self.task_id, final_status)
