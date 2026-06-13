"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from mwclient.client import Site

from ....api_services import get_user_site
from ....db.models import TemplateRecord
from ....db.services import list_templates
from ....shared.fix_nested.files_service import download_svg_file, upload_fixed_svg
from ....shared.fix_nested.objects import (
    DetectionResult,
    DownloadResult,
    VerificationResult,
)
from ....shared.fix_nested.worker import (
    detect_nested_tags,
    fix_nested_tags,
    verify_fix,
)
from ...base_worker_object import BaseObjectsJobWorker
from .objects import FixNestedMainFilesWorkerObject

logger = logging.getLogger(__name__)


def repair_nested_svg_tags(
    filename: str,
    site: Site,
) -> dict:
    """High-level orchestration for fixing nested SVG tags.

    Args:
        filename: Name of the SVG file to fix
        site: site object

    Returns:
        Dictionary with success status, message, and details.
    """
    # Use temp directory for processing
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_dir = Path(tmp_dir)

        download: DownloadResult = download_svg_file(filename, temp_dir)
        if not download.ok:
            return {
                "success": False,
                "message": f"Failed to download file: {filename}",
                "details": asdict(download),
            }

        file_path = download.path

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
                "details": asdict(verify),
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
                "details": {**asdict(verify), **upload},
            }

        return {
            "success": True,
            "message": f"Successfully fixed {verify.fixed} nested tag(s) and uploaded {filename}.",
            "details": {
                **asdict(verify),
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

    def _log_skipped_no_main_file(self, template_info: dict) -> None:
        """Log a skipped template due to the absence of a main file."""
        template_info["status"] = "skipped"
        template_info["reason"] = "No main_file set"
        self.result.pages_skipped.append(template_info)
        self.result.summary.skipped += 1

    def _log_skipped_no_nested_tags(self, template_info: dict, fix_result: dict) -> None:
        """Log information about a template that was skipped due to having no nested tags."""
        template_info["status"] = "skipped"
        template_info["reason"] = "No nested tags found"
        template_info["fix_result"] = fix_result
        self.result.pages_skipped.append(template_info)
        self.result.summary.skipped += 1

    def _log_success(self, template_info: dict, fix_result: dict) -> None:
        """Log a successfully processed template."""
        template_info["status"] = "success"
        template_info["fix_result"] = fix_result
        self.result.pages_success.append(template_info)
        self.result.summary.success += 1

    def _log_failure(self, template_info: dict, reason: str, error_type: str = "") -> None:
        """Log a template processing failure."""
        template_info["status"] = "failed"
        template_info["reason"] = reason
        if error_type:
            template_info["error_type"] = error_type
        self.result.pages_failed.append(template_info)
        self.result.summary.failed += 1

    def _log_failed_fix(self, template_info: dict, fix_result: dict) -> None:
        """Log a template that failed during processing."""
        template_info["status"] = "failed"
        template_info["reason"] = fix_result.get("message", "Unknown error")
        template_info["fix_result"] = fix_result
        self.result.pages_failed.append(template_info)
        self.result.summary.failed += 1

    def _process_one(self, template: TemplateRecord) -> None:
        self.result.summary.processed += 1

        template_info = {
            "id": template.id,
            "title": template.title,
            "main_file": template.main_file,
            "timestamp": datetime.now().isoformat(),
        }

        # Skip if template doesn't have a main_file
        if not template.main_file:
            self._log_skipped_no_main_file(template_info)
            return False

        fix_result: dict[str, Any] = {}
        try:
            # Process without job_id and db_store since we're tracking in the job
            fix_result = repair_nested_svg_tags(
                filename=template.main_file,
                site=self.site,
            )

        except Exception as e:
            self._log_failure(template_info, f"Exception: {str(e)}", type(e).__name__)
            logger.exception(f"Job {self.job_id}: Error processing template {template.title}")
            return False

        if fix_result.get("success"):
            self._log_success(template_info, fix_result)
            logger.info(f"Job {self.job_id}: Successfully processed {template.main_file}")
            return True

        elif fix_result.get("no_nested_tags", False):
            self._log_skipped_no_nested_tags(template_info, fix_result)
            logger.info(f"Job {self.job_id}: No nested tags found in {template.main_file}")
            return False
        else:
            self._log_failed_fix(template_info, fix_result)
            message = fix_result.get("message")
            logger.warning(f"Job {self.job_id}: Failed to process {template.main_file}: {message}")

        return False

    def process(self) -> FixNestedMainFilesWorkerObject:
        """Execute the fix nested tags processing logic."""
        # Get all templates

        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            return self.result

        templates = list_templates()
        self.result.summary.total = len(templates)

        logger.info(f"Job {self.job_id}: Found {len(templates)} templates")

        per_item = self.get_priority(len(templates))

        for n, template in enumerate(templates, start=1):
            logger.info(f"Job {self.job_id}: Processing template {n}/{len(templates)}: {template.title}")

            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                break

            ok = self._process_one(template)

            if ok and self.check_cancel_db_periodic():
                logger.info(f"Job {self.job_id}: Cancelled due to periodic check")
                break

            # Save progress after check for cancellation
            if n == 1 or n % per_item == 0:
                self._save_progress()

        # Update summary skipped count
        self.result.summary.skipped = len(self.result.pages_skipped)

        logger.info(
            f"Job {self.job_id} completed: "
            f"{self.result.summary.success} successful, "
            f"{self.result.summary.failed} failed, "
            f"{self.result.summary.skipped} skipped"
        )

        return self.result


def fix_nested_main_files_for_templates(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """
    Background worker to run fix_nested task on all main files from templates.

    Args:
        job_id: The job ID
        user: User authentication data for OAuth uploads
        cancel_event: Optional event to check for cancellation
        args: Optional arguments dict (unused, for unified signature)
    """
    logger.info(f"Starting job {job_id}: fix nested tags for template main files")
    worker = FixNestedMainFilesWorker(job_id, user, cancel_event)
    worker.run()


__all__ = [
    "fix_nested_main_files_for_templates",
    "FixNestedMainFilesWorker",
]
