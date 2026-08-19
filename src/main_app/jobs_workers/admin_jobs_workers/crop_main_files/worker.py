"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
from typing import Any

from mwclient.client import Site

from ....api_services import is_pages_exists
from ....database.models import TemplateRecord
from ....database.services import TemplateService
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from .files_processor import OneFileProcessor
from .objects import CropFileProcessingInfo, CropMainFilesWorkerObject
from .steps import generate_cropped_filename

logger = logging.getLogger(__name__)


class CropMainFilesWorker(BaseObjectsJobWorker):
    """
    Orchestrates the full pipeline for cropping SVG files and uploading them to Commons.

    Pipeline steps per file:
        1. Download  - fetch the original file from Commons
        2. Crop      - crop the SVG to its bounding-box
        3. Upload    - upload the cropped version under a new filename
        4. Update original  - add a link to the cropped file in the original file's wikitext
        5. Update template  - point the template page at the cropped file
        6. Update page      - point the content page at the cropped file
    """

    def __init__(self, data: JobsRunner) -> None:
        self.site: Site | None = None
        super().__init__(data)

        self.args = data.args or {}
        self.result: CropMainFilesWorkerObject = CropMainFilesWorkerObject(
            job_id=self.job_id,
            args=self.args,
        )

        self.upload_limit = self.args.get("upload_limit") or 0
        self.template_service = TemplateService()

        self.exists: dict[str, Any] = {}

        self.files_processor = OneFileProcessor(self.job_id, self.site, self.args)

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "crop_main_files"

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> CropMainFilesWorkerObject:
        """Execute the full pipeline."""

        if not self._check_site():
            return self.result

        templates = self._load_templates()

        self.result.summary.total = len(templates)
        logger.info("Job %s: Found %d templates with main files", self.job_id, len(templates))

        self._check_exists(templates)

        per_item = self.get_priority(len(templates))

        for n, template in enumerate(templates, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, len(templates), template.title)

            self.result.summary.processed += 1
            ok = self._process_one_item(template)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        if self.result.status in ["pending", "running"]:
            self.result.status = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _check_exists(self, templates) -> None:
        cropped_filenames = [generate_cropped_filename(template.last_world_file) for template in templates]
        exists_files = is_pages_exists(cropped_filenames, self.site)

        for file in exists_files:
            self.exists[file.removeprefix("File:")] = exists_files[file]

        logger.info("self.exists: %d", len(self.exists))

        self.files_processor.exists = self.exists

    def _load_templates(self) -> list[TemplateRecord]:
        templates = self.template_service.list()
        _templates = [t for t in templates if t.last_world_file]
        return self._apply_limits(_templates)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.upload_limit if isinstance(self.upload_limit, int) else 0
        if _limit > 0 and len(templates) > _limit:
            logger.info("Job %s: limiting from %d to %d item", self.job_id, len(templates), _limit)
            return templates[:_limit]

        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------
    def _process_one_item(self, template: TemplateRecord) -> bool:

        # file info
        file_info = CropFileProcessingInfo.from_template(template)

        ok = self.files_processor.process_one_item(file_info, template)

        self.update_status(file_info)

        return ok

    def update_status(self, info: CropFileProcessingInfo) -> None:
        if info.status.lower() in ["pending", "running"]:
            info.status = "completed"

        if info.status == "updated":
            self.result.summary.updated += 1
            self.result.pages_updated.append(info)

        elif info.status == "uploaded":
            self.result.summary.uploaded += 1
            self.result.pages_uploaded.append(info)

        elif info.status == "skipped":
            self.result.summary.skipped += 1
            self.result.pages_skipped.append(info)

        elif info.status == "failed":
            self.result.summary.failed += 1
            self.result.pages_failed.append(info)
        else:
            self.result.pages_processed.append(info)

        if info.steps.crop.result is True:
            self.result.summary.cropped += 1


__all__ = [
    "CropMainFilesWorker",
]
