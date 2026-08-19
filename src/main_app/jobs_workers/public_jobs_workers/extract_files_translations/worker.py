"""
Worker module for extract_files_translations.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from mwclient.client import Site

from ....api_services.files_service import DownloadAndSaveData, FilesService
from ....config import settings
from ....services.copysvg_wrapper import (
    ExtractResult,
    extract_from_path,
)
from ....services.copysvg_wrapper.mapping import ExtractorData
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from ..copy_svg_langs.steps import (
    extract_text_step,
    extract_titles_step,
)
from .objects import (
    ExtractFilesTranslationsObject,
    FilesProcessedItem,
)

logger = logging.getLogger(__name__)


class ExtractFilesTranslationsWorker(BaseObjectsJobWorker):
    """
    Worker for copying SVG translations from a main file to its versions.
    """

    def __init__(self, data: JobsRunner) -> None:
        super().__init__(data)
        args = data.args or {}

        self.result: ExtractFilesTranslationsObject = ExtractFilesTranslationsObject(
            job_id=self.job_id,
            args=args,
        )

        self.title = args["title"].strip() if args.get("title") else None

        self.output_dir = self._compute_output_dir(self.title)
        self.output_dir_files = (self.output_dir / "files") if self.output_dir else None

        self.overwrite_download = True
        self.site: Site | None = None
        self.text: str = ""
        self.titles: list[str] = []
        self.files_service = FilesService()
        self.mapping: ExtractorData = ExtractorData()

    def _compute_output_dir(self, title: str) -> Path:
        if not title:
            return None

        name = Path(title).name
        slug = re.sub(r"[^A-Za-z0-9._\- ]+", "_", str(name)).strip("._") or "untitled"
        slug = slug.replace(" ", "_").lower()
        out = Path(settings.paths.svg_data) / slug
        out.mkdir(parents=True, exist_ok=True)

        out_dir_main = out / "files"
        out_dir_main.mkdir(parents=True, exist_ok=True)

        return out

    def _extract_titles_step(self) -> bool:
        stage = self.result.stages.titles

        if self.is_cancelled():
            stage.status = "cancelled"
            return False

        stage.status = "running"
        self.save_result()

        try:
            step_result = extract_titles_step(self.text)

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

            self.titles = list(step_result["titles"])

            if step_result["main_title"] not in self.titles:
                self.titles.append(step_result["main_title"])

            self.titles.sort()

            return True

        stage.status = "failed"
        stage.message = step_result.get("error", "Unknown error")
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

    # ------------------

    def one_file(self, title_info: FilesProcessedItem) -> None:
        # ----------------------------------------------
        # File step 1: download
        file_path_str: str | None = self.get_file_path(title_info)

        if not file_path_str:
            return

        title_info.file_path = file_path_str

        self.extract_file_translations(title_info)

    # ------------------

    def process_titles(self, title_to_work: list[str]) -> None:
        processfiles_stage = self.result.stages.processfiles
        processfiles_stage.status = "running"

        per_item = self.get_priority(len(title_to_work))

        for n, title in enumerate(title_to_work, start=1):
            processfiles_stage.message = f"Processing files {n}/{len(title_to_work)}"
            logger.info("Job %s: Processing title %d/%d: %s", self.job_id, n, len(title_to_work), title)

            if self.is_cancelled():
                logger.info("Job %s: Cancellation detected, stopping.", self.job_id)
                processfiles_stage.status = "cancelled"
                break

            title_info = FilesProcessedItem(title=title)

            self.one_file(title_info)

            if title_info.is_mapping_merged:
                self.result.mapping_mereged += 1

            self.update_status(title_info)

            if self.is_cancelled():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self.save_result()

        if processfiles_stage.status in ["pending", "running"]:
            processfiles_stage.status = "completed"

    def extract_file_translations(self, title_info: FilesProcessedItem) -> None:
        langs_step = title_info.steps.languages
        mapping_step = title_info.steps.load_mapping

        file_path = Path(title_info.file_path)
        try:
            result: ExtractResult = extract_from_path(file_path, fast_return_false=False)
        except Exception as e:
            logger.error("Error in extract translations")
            mapping_step._update(result=False, details={"error": str(e)}, msg="Error in extract translations")
            langs_step._update(result=None)  # skipped
            return

        mapping = result.mapping

        if not mapping or mapping.is_empty():
            title_info.status = "failed"
            title_info.error = "File doesn't contain any translations"
            return

        data = {
            "new": len(mapping.new),
            "title_new": len(mapping.title_new),
        }

        mapping_step._update(result=True, msg="extract translations success", details=data)

        if not result.success:
            title_info.status = "failed"
            title_info.error = "failed to extract translations"
            return

        title_info.status = "success"
        langs_step._update(
            result=True, details={"languages": sorted(mapping.all_languages())}, msg="extract languages success"
        )

        self.update_translations(mapping)
        title_info.is_mapping_merged = True
        return

    def get_file_path(self, title_info: FilesProcessedItem) -> None | str:
        down_step = title_info.steps.download
        try:
            file_data: DownloadAndSaveData = self.files_service.download_and_save(
                title=title_info.title,
                out_dir=self.output_dir_files,
                overwrite_download=self.overwrite_download,
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

    # ------------------
    # Public API
    # ------------------

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "extract_files_translations"

    def process(self) -> ExtractFilesTranslationsObject:
        """Execute the full pipeline."""
        if not self._check_site():
            return self.result

        if not self.title:
            logger.error("No title found")
            self.result.status = "failed"
            return self.result

        self.result.title = self.title
        # ----------------------------------------------
        # Stage 1: Extract Text

        self.save_result()

        if not self._extract_text_step():
            return self.result

        # ----------------------------------------------
        # Stage 2: Extract Titles
        # which is used in extract_translations

        if not self._extract_titles_step():
            return self.result

        self.result.summary.total = len(self.titles)

        self.process_titles(self.titles)

        # save mapping to file
        self._save_mapping(self.job_id)

        return self.result

    def _save_mapping(self, job_id: int) -> None:
        mapping_path = self.output_dir
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

    def update_translations(self, mapping: ExtractorData) -> None:
        if mapping.is_empty():
            return

        if self.mapping is None:
            self.mapping = mapping
            return

        self.mapping.merge(mapping, merge_keys=["new", "title_new"])
        self.result.languages = sorted(self.mapping.all_languages())

    def save_result(self):
        # save mapping to file
        self._save_mapping(self.job_id)
        self.result.mapping = self.mapping.to_json()

        self._save_progress()

    def update_status(self, info: FilesProcessedItem):
        self.result.summary.processed +=  1

        if info.status.lower() in ["pending", "running"]:
            info.status = "completed"

        if info.status == "success":
            self.result.files_success.append(info)

        elif info.status == "failed":
            self.result.files_failed.append(info)
        else:
            self.result.files_processed.append(info)


__all__ = [
    "ExtractFilesTranslationsWorker",
]
