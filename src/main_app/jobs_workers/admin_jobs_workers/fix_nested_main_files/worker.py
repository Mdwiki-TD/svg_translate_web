"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Any

from mwclient.client import Site

from ....api_services import FilesService, UploadService
from ....database.services import TemplateService
from ....services.copysvg_wrapper import NestedStructureService
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from .objects import FixNestedMainFilesWorkerObject, TitleInfo

logger = logging.getLogger(__name__)


class FixNestedMainFilesWorker(BaseObjectsJobWorker):
    """Worker for fixing nested tags in main files of templates."""

    def __init__(self, data: JobsRunner) -> None:
        super().__init__(data)
        self.args = data.args or {}

        self.result: FixNestedMainFilesWorkerObject = FixNestedMainFilesWorkerObject(
            job_id=self.job_id,
            args=self.args,
        )
        self.site: Site | None = None
        self.files_service = FilesService()
        self.upload_service = UploadService(self.site)
        self.fix_nested_processer = NestedStructureService(
            strategy="flatten",
        )

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "fix_nested_main_files"

    def _process_one_item(self, template_info: TitleInfo) -> bool:

        # Skip if template doesn't have a main_file
        if not template_info.main_file:
            template_info._update("skipped", "No main_file set")
            return False

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)
            # Process without job_id and db_store since we're tracking in the job
            fix_result = self.repair_nested_svg_tags(
                filename=template_info.main_file,
                temp_dir=temp_dir,
            )

        template_info.fix_result = fix_result

        if fix_result.get("success"):
            template_info._update("success", "")
            logger.info("Job %s: Successfully processed %s", self.job_id, template_info.main_file)
            return True

        elif fix_result.get("no_nested_tags", False):
            template_info._update("skipped", "No nested tags found")
            logger.info("Job %s: No nested tags found in %s", self.job_id, template_info.main_file)
            return False

        message = fix_result.get("message", "Unknown error")
        template_info._update("failed", message)
        logger.warning("Job %s: Failed to process %s: %s", self.job_id, template_info.main_file, message)

        return False

    def process(self) -> FixNestedMainFilesWorkerObject:
        """Execute the fix nested tags processing logic."""
        # Get all templates

        if not self._check_site():
            return self.result

        # update site after calling _check_site
        if self.site is None:
            raise ValueError("Site is not set")

        self.upload_service.site = self.site

        templates = TemplateService().list()
        self.result.summary.total = len(templates)

        logger.info("Job %s: Found %d templates", self.job_id, len(templates))

        per_item = self.get_priority(len(templates))

        for n, template in enumerate(templates, start=1):
            logger.info("Job %s: Processing template %d/%d: %s", self.job_id, n, len(templates), template.title)

            if self.is_cancelled():
                logger.info("Job %s: Cancellation detected, stopping.", self.job_id)
                break

            template_info = TitleInfo.from_template(template)

            ok = self._process_one_item(template_info)
            self.update_status(template_info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self._save_progress()

        logger.info(
            "Job %s completed: %d successful, %d skipped, %d failed",
            self.job_id,
            len(self.result.pages_success),
            len(self.result.pages_skipped),
            len(self.result.pages_failed),
        )

        return self.result

    def repair_nested_svg_tags(
        self,
        filename: str,
        temp_dir: Path,
    ) -> dict[str, Any]:
        """High-level orchestration for fixing nested SVG tags.

        Args:
            filename: Name of the SVG file to fix

        Returns:
            Dictionary with success status, message, and details.
        """
        # Use temp directory for processing
        try:
            download = self.files_service.download_and_save(filename, temp_dir)
        except Exception as e:
            logger.exception("Error downloading SVG file")
            return {
                "success": False,
                "message": f"Error downloading {filename}",
                "details": str(e),
            }

        if download.result != "success":
            return {
                "success": False,
                "message": f"Failed to download file: {filename}",
                "details": download,
            }

        file_path = download.path

        detect_before = self.fix_nested_processer.analyze_file(file_path)

        if len(detect_before) == 0:
            return {
                "success": False,
                "message": f"No nested tags found in {filename}",
                "details": {"nested_count": 0},
                "no_nested_tags": True,
            }
        fixed = self.fix_nested_processer.repair_file(file_path)
        if not fixed.success:
            return {
                "success": False,
                "message": f"Failed to fix nested tags in {filename}",
                "details": {"nested_count": len(detect_before)},
            }

        verify = verify = {
            "before": fixed.len_tags_before_fix,
            "after": fixed.len_tags_after_fix,
            "fixed": fixed.len_tags_fixed,
        }

        if fixed.len_tags_fixed == 0:
            return {
                "success": False,
                "message": f"No nested tags were fixed in {filename}",
                "details": verify,
            }

        if fixed.len_tags_after_fix != 0:
            return {
                "success": False,
                "message": f"Fixed {fixed.len_tags_fixed} nested tag(s), but {fixed.len_tags_after_fix} nested tag(s) remain",
                "details": verify,
            }

        summary = f"Fixed {fixed.len_tags_fixed} nested tag(s)"

        upload = self.upload_service.upload_svg(
            filename,
            file_path,
            summary,
        )

        if not upload.ok:
            return {
                "success": False,
                "message": f"Fixed {fixed.len_tags_fixed} nested tag(s), but upload failed.",
                "details": {**verify, **upload.to_json()},
            }

        return {
            "success": True,
            "message": f"Successfully fixed {fixed.len_tags_fixed} nested tag(s) and uploaded {filename}.",
            "details": {
                **verify,
                "upload_result": upload.result,
            },
        }

    def update_status(self, info: TitleInfo) -> None:
        self.result.summary.processed += 1

        if info.status in ["pending", "running"]:
            info.status = "completed"

        elif info.status == "skipped":
            self.result.pages_skipped.append(info)

        elif info.status == "success":
            self.result.pages_success.append(info)

        elif info.status == "failed":
            self.result.pages_failed.append(info)


__all__ = [
    "FixNestedMainFilesWorker",
]
