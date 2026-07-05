"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from mwclient.client import Site

from ....api_services import download_svg_file, upload_fixed_svg
from ....db.models import TemplateRecord
from ....db.services import list_templates
from ....shared.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
    detect_nested_tags,
    fix_nested_tags,
    verify_fix,
)
from ...base_worker import BaseObjectsJobWorker
from .objects import FixNestedMainFilesWorkerObject, TemplateInfo

logger = logging.getLogger(__name__)


def repair_nested_svg_tags(
    filename: str,
    site: Site,
    temp_dir: Path,
) -> dict:
    """High-level orchestration for fixing nested SVG tags.

    Args:
        filename: Name of the SVG file to fix
        site: site object

    Returns:
        Dictionary with success status, message, and details.
    """
    # Use temp directory for processing
    try:
        download = download_svg_file(filename, temp_dir)
    except Exception as e:
        logger.exception("Error downloading SVG file")
        return {
            "success": False,
            "message": f"Error downloading {filename}",
            "details": str(e),
        }

    if not download.get("ok"):
        return {
            "success": False,
            "message": f"Failed to download file: {filename}",
            "details": download,
        }

    file_path = download.get("path")

    detect_before: DetectionResult = detect_nested_tags(file_path)

    if detect_before.count == 0:
        return {
            "success": False,
            "message": f"No nested tags found in {filename}",
            "details": {"nested_count": 0},
            "no_nested_tags": True,
        }

    if not fix_nested_tags(file_path):
        return {
            "success": False,
            "message": f"Failed to fix nested tags in {filename}",
            "details": {"nested_count": detect_before.count},
        }

    verify: VerificationResult = verify_fix(file_path, detect_before.count)

    if verify.fixed == 0:
        return {
            "success": False,
            "message": f"No nested tags were fixed in {filename}",
            "details": verify.to_dict(),
        }

    upload = upload_fixed_svg(
        filename,
        file_path,
        verify.fixed,
        site,
    )

    if not upload.get("ok"):
        return {
            "success": False,
            "message": f"Fixed {verify.fixed} nested tag(s), but upload failed.",
            "details": {**verify.to_dict(), **upload},
        }

    return {
        "success": True,
        "message": f"Successfully fixed {verify.fixed} nested tag(s) and uploaded {filename}.",
        "details": {
            **verify.to_dict(),
            "upload_result": upload.get("result"),
        },
    }


class FixNestedMainFilesWorker(BaseObjectsJobWorker):
    """Worker for fixing nested tags in main files of templates."""

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(job_id, user, cancel_event)
        self.result: FixNestedMainFilesWorkerObject = FixNestedMainFilesWorkerObject()
        self.args = args or {}
        self.result.args = self.args
        self.site: Site | None = None

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "fix_nested_main_files"

    def _process_one_item(self, template: TemplateRecord) -> bool:
        self.result.summary.processed += 1

        template_info = TemplateInfo(
            id=template.id,
            title=template.title,
            main_file=template.main_file,
            timestamp=datetime.now().isoformat(),
        )

        # Skip if template doesn't have a main_file
        if not template.main_file:
            template_info._update("skipped", "No main_file set")
            self.result.pages_skipped.append(template_info)
            return False

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)
            # Process without job_id and db_store since we're tracking in the job
            fix_result = repair_nested_svg_tags(
                filename=template.main_file,
                site=self.site,
                temp_dir=temp_dir,
            )

        template_info.fix_result = fix_result

        if fix_result.get("success"):
            template_info._update("success", "")

            self.result.pages_success.append(template_info)
            logger.info("Job %s: Successfully processed %s", self.job_id, template.main_file)
            return True

        elif fix_result.get("no_nested_tags", False):
            template_info._update("skipped", "No nested tags found")

            self.result.pages_skipped.append(template_info)

            logger.info("Job %s: No nested tags found in %s", self.job_id, template.main_file)
            return False

        message = fix_result.get("message", "Unknown error")
        template_info._update("failed", message)

        self.result.pages_failed.append(template_info)
        logger.warning("Job %s: Failed to process %s: %s", self.job_id, template.main_file, message)

        return False

    def process(self) -> FixNestedMainFilesWorkerObject:
        """Execute the fix nested tags processing logic."""
        # Get all templates

        if not self._check_site():
            return self.result

        templates = list_templates()
        self.result.summary.total = len(templates)

        logger.info("Job %s: Found %d templates", self.job_id, len(templates))

        per_item = self.get_priority(len(templates))

        for n, template in enumerate(templates, start=1):
            logger.info("Job %s: Processing template %d/%d: %s", self.job_id, n, len(templates), template.title)

            if self.is_cancelled():
                logger.info("Job %s: Cancellation detected, stopping.", self.job_id)
                break

            ok = self._process_one_item(template)

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


__all__ = [
    "FixNestedMainFilesWorker",
]
