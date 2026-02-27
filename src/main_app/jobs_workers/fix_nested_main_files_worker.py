"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ..config import settings
from ..template_service import get_templates_db_bg
from ..app_routes.fix_nested.fix_utils import (
    detect_nested_tags,
    download_svg_file,
    fix_nested_tags,
    upload_fixed_svg,
    verify_fix,
)
from .base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


def repair_nested_svg_tags(
    filename: str,
    user,
    cancel_event: threading.Event | None = None,
) -> dict:
    """High-level orchestration for fixing nested SVG tags.

    Args:
        filename: Name of the SVG file to fix
        user: User object for authentication during upload
        cancel_event: Optional event to check for cancellation
    """
    # Use temp directory for processing
    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_dir = Path(tmp_dir)

        download = download_svg_file(filename, temp_dir)
        if not download["ok"]:
            return {
                "success": False,
                "message": f"Failed to download file: {filename}",
                "details": download,
            }

        file_path = download["path"]

        if cancel_event and cancel_event.is_set():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        detect_before = detect_nested_tags(file_path)

        if detect_before["count"] == 0:
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
                "details": {"nested_count": detect_before["count"]},
            }

        if cancel_event and cancel_event.is_set():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        verify = verify_fix(file_path, detect_before["count"])

        if verify["fixed"] == 0:
            return {
                "success": False,
                "message": f"No nested tags were fixed in {filename}",
                "details": verify,
            }

        if cancel_event and cancel_event.is_set():
            return {"success": False, "message": "Cancelled", "cancelled": True}

        upload = upload_fixed_svg(filename, file_path, verify["fixed"], user)

        if not upload["ok"]:
            return {
                "success": False,
                "message": f"Fixed {verify['fixed']} nested tag(s), but upload failed.",
                "details": {**verify, **upload},
            }

        return {
            "success": True,
            "message": f"Successfully fixed {verify['fixed']} nested tag(s) and uploaded {filename}.",
            "details": {
                **verify,
                "upload_result": upload["result"],
            },
        }


class FixNestedMainFilesWorker(BaseJobWorker):
    """Worker for fixing nested tags in main files of templates."""

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "fix_nested_main_files"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "templates_processed": [],
            "templates_success": [],
            "templates_failed": [],
            "templates_skipped": [],
            "summary": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "no_main_file": 0,
            },
        }

    def _log_skipped_no_main_file(self, template_info: dict) -> None:
        """Log a skipped template due to the absence of a main file."""
        template_info["status"] = "skipped"
        template_info["reason"] = "No main_file set"
        self.result["templates_skipped"].append(template_info)
        self.result["summary"]["no_main_file"] += 1

    def _log_skipped_no_nested_tags(self, template_info: dict, fix_result: dict) -> None:
        """Log information about a template that was skipped due to having no nested tags."""
        template_info["status"] = "skipped"
        template_info["reason"] = "No nested tags found"
        template_info["fix_result"] = fix_result
        self.result["templates_skipped"].append(template_info)
        self.result["summary"]["skipped"] += 1

    def _log_success(self, template_info: dict, fix_result: dict) -> None:
        """Log a successfully processed template."""
        template_info["status"] = "success"
        template_info["fix_result"] = fix_result
        self.result["templates_success"].append(template_info)
        self.result["summary"]["success"] += 1

    def _log_failure(self, template_info: dict, reason: str, error_type: str = "") -> None:
        """Log a template processing failure."""
        template_info["status"] = "failed"
        template_info["reason"] = reason
        if error_type:
            template_info["error_type"] = error_type
        self.result["templates_failed"].append(template_info)
        self.result["summary"]["failed"] += 1

    def _log_failed_fix(self, template_info: dict, fix_result: dict) -> None:
        """Log a template that failed during processing."""
        template_info["status"] = "failed"
        template_info["reason"] = fix_result.get("message", "Unknown error")
        template_info["fix_result"] = fix_result
        self.result["templates_failed"].append(template_info)
        self.result["summary"]["failed"] += 1

    def process(self) -> Dict[str, Any]:
        """Execute the fix nested tags processing logic."""
        from . import jobs_service

        result = self.result

        # Get all templates
        templates_db = get_templates_db_bg()
        templates = templates_db.list()
        result["summary"]["total"] = len(templates)

        logger.info(f"Job {self.job_id}: Found {len(templates)} templates")

        for n, template in enumerate(templates, start=1):
            logger.info(f"Job {self.job_id}: Processing template {n}/{len(templates)}: {template.title}")

            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                break

            # Save progress after check for cancellation
            if n == 1 or n % 10 == 0:
                try:
                    jobs_service.save_job_result_by_name(self.result_file, result)
                except Exception:
                    logger.exception(f"Job {self.job_id}: Failed to save progress")

            template_info = {
                "id": template.id,
                "title": template.title,
                "main_file": template.main_file,
                "timestamp": datetime.now().isoformat(),
            }

            # Skip if template doesn't have a main_file
            if not template.main_file:
                self._log_skipped_no_main_file(template_info)
                continue

            fix_result = {}
            try:
                # Process without task_id and db_store since we're tracking in the job
                fix_result = repair_nested_svg_tags(
                    filename=template.main_file,
                    user=self.user,
                    cancel_event=self.cancel_event,
                )

            except Exception as e:
                self._log_failure(template_info, f"Exception: {str(e)}", type(e).__name__)
                logger.exception(f"Job {self.job_id}: Error processing template {template.title}")
                continue

            if fix_result.get("cancelled"):
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                result["status"] = "cancelled"
                result["cancelled_at"] = datetime.now().isoformat()
                break

            if fix_result["success"]:
                self._log_success(template_info, fix_result)
                logger.info(f"Job {self.job_id}: Successfully processed {template.main_file}")

            elif fix_result.get("no_nested_tags", False):
                self._log_skipped_no_nested_tags(template_info, fix_result)
                logger.info(f"Job {self.job_id}: No nested tags found in {template.main_file}")

            else:
                self._log_failed_fix(template_info, fix_result)
                logger.warning(
                    f"Job {self.job_id}: Failed to process {template.main_file}: "
                    f"{fix_result.get('message')}"
                )

        # Update summary skipped count
        result["summary"]["skipped"] = len(result["templates_skipped"])

        logger.info(
            f"Job {self.job_id} completed: "
            f"{result['summary']['success']} successful, "
            f"{result['summary']['failed']} failed, "
            f"{result['summary']['skipped']} skipped"
        )

        return result


def fix_nested_main_files_for_templates(
    job_id: int,
    user: Dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Background worker to run fix_nested task on all main files from templates.

    This function:
    1. Fetches all templates from the database
    2. For each template with a main_file:
       - Runs the fix_nested process (download, fix, upload)
       - Uses the user's OAuth credentials for file uploads
    3. Saves a detailed report to a JSON file

    Args:
        job_id: The job ID
        user: User authentication data for OAuth uploads
        cancel_event: Optional event to check for cancellation
    """
    logger.info(f"Starting job {job_id}: fix nested tags for template main files")
    worker = FixNestedMainFilesWorker(job_id, user, cancel_event)
    worker.run()


__all__ = [
    "fix_nested_main_files_for_templates",
    "FixNestedMainFilesWorker",
]
