"""
Worker module for copy_svg_langs.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from mwclient.client import Site

from ....api_services.files_service import FilesService
from ....config import settings
from ....services.copysvg_wrapper import (
    ExtractResult,
    extract_from_path,
)
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from .files_worker import OneFileProcessor
from .objects import (
    CopySvgLangsWorkerObject,
    FilesProcessedItem,
    SvgLangsConfig,
)
from .steps import (
    extract_text_step,
    extract_titles_step,
)

logger = logging.getLogger(__name__)


class CopySvgLangsWorker(BaseObjectsJobWorker):
    """
    Worker for copying SVG translations from a main file to its versions.
    """

    def __init__(self, data: JobsRunner) -> None:
        super().__init__(data)
        args = data.args or {}

        self.result: CopySvgLangsWorkerObject = CopySvgLangsWorkerObject(
            job_id=self.job_id,
            args=args,
        )

        self.title = args["title"].strip() if args.get("title") else None
        self.manual_main_title = args["manual_main_title"].strip() if args.get("manual_main_title") else None

        self.config = self._load_config(args)
        self.site: Site | None = None
        self.text: str = ""
        self.main_title: str = ""
        self.titles: list[str] = []
        self.files_service = FilesService()

        self.files_processor = OneFileProcessor(self.config, self.files_service)

    def _load_config(self, args: dict[str, Any]) -> SvgLangsConfig:
        output_dir = self._compute_output_dir(self.title)
        output_dir_files = (output_dir / "files") if output_dir else None

        try:
            limit_items = int(args.get("limit_items")) or 0
        except Exception:
            limit_items = 0

        upload_limit = args.get("upload_limit") or 0
        upload_limit = upload_limit if isinstance(upload_limit, int) else 0

        overwrite_translations = bool(args.get("overwrite_translations"))

        overwrite_download = True

        # if args.get("overwrite_download") is not None: overwrite_download = bool(args.get("overwrite_download"))

        return SvgLangsConfig(
            upload=args.get("upload"),
            upload_files=args.get("upload_files"),
            upload_limit=upload_limit,
            limit_items=limit_items,
            overwrite_translations=overwrite_translations,
            overwrite_download=overwrite_download,
            output_dir=output_dir,
            output_dir_files=output_dir_files,
        )

    def _apply_limits(self, titles: list[str]) -> list[str]:
        _limit = self.config.limit_items
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
                manual_main_title=self.manual_main_title,
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
        output_dir_main = self.config.output_dir_files

        main_file_download = self.files_service.download_and_save(
            title=self.main_title,
            out_dir=output_dir_main,
            overwrite_download=self.config.overwrite_download,
        )

        if main_file_download.result != "success" or not main_file_download.path:
            error = f"Error when downloading main file: {self.main_title}, error: {main_file_download.error}"
            logger.error(error)
            stage.status = "failed"
            stage.message = error
            self.result.status = "failed"

            return False

        main_title_path = main_file_download.path

        try:
            step_result: ExtractResult = extract_from_path(main_title_path)
        except Exception as e:
            logger.exception("Error in stage translations")
            stage.status = "failed"
            stage.message = str(e)
            self.result.status = "failed"
            return False

        mapping = step_result.mapping

        new_translations = mapping.new if mapping else {}

        languages = sorted(mapping.all_languages()) if mapping else []

        self.result.translations = self._render_new_translations(new_translations, languages)
        self.result.languages = languages

        if step_result.success and mapping:
            stage.status = "completed"
            stage.message = step_result.message or f"Loaded translations from (File:{self.main_title})"
            self.files_processor.update_translations(mapping)
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

    def _process_one_item(self, title_info: FilesProcessedItem, main_title: str) -> bool:
        return self.files_processor.process_one_item(title_info, main_title)

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

            self.result.summary.processed += 1
            ok = self._process_one_item(title_info, self.main_title)

            if title_info.is_mapping_merged:
                self.result.mapping_mereged += 1

            self.update_status(title_info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self._save_progress()

        if processfiles_stage.status in ["pending", "running"]:
            processfiles_stage.status = "completed"

    # ------------------
    # Public API
    # ------------------

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "copy_svg_langs"

    def process(self) -> CopySvgLangsWorkerObject:
        """Execute the full pipeline."""
        if not self._check_site():
            return self.result

        # update site after calling _check_site
        if self.site is None:
            raise ValueError("Site is not set")

        self.files_processor.upload_service.site = self.site

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

        self.result.summary.total = len(self.titles)
        title_to_work = self._apply_limits(self.titles)

        self.process_titles(title_to_work)

        return self.result

    def after_run(self) -> None:

        if self.config.merge_mapping_all_files:
            # save mapping to file
            self.files_processor._save_mapping(self.job_id)

        super().after_run()

    def update_status(self, info: FilesProcessedItem):
        if info.status.lower() in ["pending", "running"]:
            info.status = "completed"

        if info.status == "success":
            self.result.files_success.append(info)

        elif info.status == "skipped":
            self.result.files_skipped.append(info)

        elif info.status == "failed":
            self.result.files_failed.append(info)
        else:
            self.result.files_processed.append(info)


__all__ = [
    "CopySvgLangsWorker",
]
