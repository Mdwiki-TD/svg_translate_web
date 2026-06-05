"""
Worker module for fix_nested_jobs.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import mwclient
import requests

from ...api_services.clients import create_commons_session, get_user_site
from ...config import settings
from ...db.services import is_job_cancelled
from ...jobs_workers.base_worker import BaseJobWorker
from ...shared.fix_nested.worker import (
    detect_nested_tags,
    download_svg_file,
    fix_nested_tags,
    upload_fixed_svg,
    verify_fix,
)
from ...su_services import jobs_files_service

logger = logging.getLogger(__name__)


@dataclass
class FixNestedJobsProcessor:
    """
    Orchestrates the pipeline for fixing nested tags in SVG files.
    """

    job_id: str | int
    args: Any
    user: dict[str, Any]
    result: dict[str, Any]
    result_file: str
    cancel_event: threading.Event | None = None

    site: mwclient.Site | None = field(init=False, default=None)
    session: requests.Session | None = field(init=False, default=None)

    filename: str = None

    def __post_init__(self) -> None:
        self.filename = self.args.get("filename")

    def _save_progress(self) -> None:
        try:
            result = self.result
            result["last_update"] = datetime.now().isoformat()
            jobs_files_service.save_job_result_by_name(self.result_file, result)
        except Exception:
            logger.exception(f"Job {self.job_id}: Failed to save progress")

    def _is_cancelled(self, stage_name: str | None = None) -> bool:
        cancelled = False
        if self.cancel_event and self.cancel_event.is_set():
            cancelled = True
        elif is_job_cancelled(self.job_id, job_type="fix_nested_jobs"):
            cancelled = True

        if cancelled:
            self.result["status"] = "Cancelled"
            if self.result.get("cancelled_at") is None:
                self.result["cancelled_at"] = datetime.now().isoformat()
            if stage_name and stage_name in self.result.get("stages", {}):
                self.result["stages"][stage_name]["status"] = "Cancelled"
            return True
        return False

    def _update_step(self, stage_name: str, status: str, message: str) -> None:
        self.result["stages"][stage_name]["status"] = status
        self.result["stages"][stage_name]["message"] = message

    def run(self) -> dict[str, Any]:
        """Execute the full pipeline."""
        self.result["status"] = "running"
        self._save_progress()

        self.session = create_commons_session(settings.other.user_agent)
        self.site = get_user_site(self.user)

        if not self.filename:
            logger.error("No filename found")
            self.result["status"] = "Failed"
            return self.result

        self.result["filename"] = self.filename

        # ----------------------------------------------
        # Stage 1: Download SVG files

        if not self._run_stage("download", self._download_step):
            return self.result

        # ----------------------------------------------
        # Stage 2: Analyze nested tags
        if not self._run_stage("analyze", self._analyze_step):
            return self.result

        # ----------------------------------------------
        # Stage 3: Fix nested tags
        if not self._run_stage("fix", self._fix_step):
            return self.result

        # ----------------------------------------------
        # Stage 4: Verify fixes
        if not self._run_stage("verify", self._verify_step):
            return self.result

        # ----------------------------------------------
        # Stage 5: Upload fixed files

        if not self._run_stage("upload", self._upload_step):
            return self.result

        # ----------------------------------------------
        # Finalize
        self.result["status"] = "completed"
        self.result["completed_at"] = datetime.now().isoformat()
        self._save_progress()

        return self.result

    def _download_step(self) -> bool | None:
        """Download SVG files from Commons."""

        temp_dir = Path(tempfile.gettempdir())

        download_result = download_svg_file(self.filename, temp_dir)

        if download_result["ok"]:
            self._update_step("download", "success", "Downloaded success")
            self.result["file_result"] = {
                "success": True,
                "status": "success",
                "path": str(download_result["path"]),
                "error": None,
            }
            return True

        self._update_step("download", "Failed", "Downloaded Failed")

        # Update stage message
        self.result["file_result"] = {
            "success": False,
            "status": "Failed",
            "path": None,
            "error": download_result.get("error", "download_failed"),
        }

        return False

    def _analyze_step(self) -> bool | None:
        """Analyze nested tags in downloaded files."""

        if self.result["stages"]["download"]["status"] != "success" or not self.result["file_result"].get("path"):
            self._update_step("analyze", "skipped", "download step Failed")
            return None

        file_path = Path(self.result["file_result"]["path"])
        if not file_path.is_file():
            self._update_step("analyze", "Failed", "File not found")
            return False

        detect_result = detect_nested_tags(file_path)

        self.result["file_result"]["nested_tags_before"] = detect_result["count"]
        self.result["file_result"]["nested_tags"] = detect_result["tags"]

        if detect_result["count"] == 0:
            self._update_step("analyze", "skipped", "No nested tags found")
            return None

        analyze_message = f"Found {detect_result['count']} nested tags"
        self._update_step("analyze", "success", analyze_message)

        return True

    def _fix_step(self) -> bool | None:
        """Fix nested tags in files."""

        if self.result["stages"]["analyze"]["status"] != "success":
            self._update_step("fix", "skipped", self.result["stages"]["analyze"]["message"] or "skipped")
            return None

        file_path = Path(self.result["file_result"]["path"])
        fix_success = fix_nested_tags(file_path)

        if fix_success:
            self._update_step("fix", "success", "Nested tags fixed successfully")
            return True

        self._update_step("fix", "Failed", "Failed to fix nested tags")
        return False

    def _verify_step(self) -> bool | None:
        """Verify that nested tags were fixed."""

        if self.result["stages"]["fix"]["status"] != "success":
            self._update_step("verify", "skipped", "fix failed")
            return None

        file_path = Path(self.result["file_result"]["path"])
        before_count = self.result["file_result"].get("nested_tags_before", 0)
        verify_result = verify_fix(file_path, before_count)

        self.result["file_result"]["nested_tags_after"] = verify_result["after"]
        self.result["file_result"]["nested_tags_fixed"] = verify_result["fixed"]

        if verify_result["fixed"] > 0:
            message = f"Verified: {verify_result['fixed']} tags fixed"
            self._update_step("verify", "success", message)
            return True

        message = "No tags were fixed"
        self._update_step("verify", "Failed", message)

        return False

    def _upload_step(self) -> bool | None:
        """Upload fixed files to Commons."""

        upload_enabled = self.args.get("upload", True)
        if not upload_enabled:
            self._update_step("upload", "skipped", "Upload disabled")
            return None

        if not self.site:
            self._update_step("upload", "Failed", "Authentication failed")
            return None

        if self.result["stages"]["verify"]["status"] != "success":
            self._update_step("upload", "skipped", "Skipped (not fixed)")
            return None

        file_path = Path(self.result["file_result"]["path"])
        tags_fixed = self.result["file_result"].get("nested_tags_fixed", 0)

        upload_result = upload_fixed_svg(
            self.filename,
            file_path,
            tags_fixed,
            self.user,
        )

        if upload_result["ok"]:
            self._update_step("upload", "success", "Uploaded successfully")
            return True

        message = upload_result.get("error", "Upload failed")

        self._update_step("upload", "Failed", message)

        return False

    def _run_stage(
        self,
        stage_name: str,
        step_func: Any,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Run a single stage and update result."""
        if self._is_cancelled(stage_name):
            return False

        stage = self.result["stages"][stage_name]
        stage["status"] = "Running"
        self._save_progress()

        try:
            step_result = step_func(*args, **kwargs)
            if step_result:
                return True
            elif step_result is False:
                self.result["status"] = "Failed"
                return False
            else:
                self.result["status"] = "skipped"
                return False

        except Exception as e:
            logger.exception(f"Error in stage {stage_name}")
            stage["status"] = "Failed"
            stage["message"] = str(e)
            self.result["status"] = "Failed"
            return False


class FixNestedJobsWorker(BaseJobWorker):
    """
    Worker for fixing nested tags in user-submitted SVG files.
    """

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args or {}

        super().__init__(job_id, user, cancel_event)
        self.result: Dict[str, Any] = self.get_initial_result()

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "fix_nested_jobs"

    def get_initial_result(self) -> dict[str, Any]:
        """Return the initial result structure."""
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "filename": None,
            "file_result": {
                "status": "pending",
                "path": None,
                "error": None,
            },
            "stages": {
                "download": {"status": "Pending", "message": "Downloading files"},
                "analyze": {"status": "Pending", "message": "Analyzing nested tags"},
                "fix": {"status": "Pending", "message": "Fixing nested tags"},
                "verify": {"status": "Pending", "message": "Verifying fixes"},
                "upload": {"status": "Pending", "message": "Uploading fixed files"},
            },
        }

    def process(self) -> dict[str, Any]:
        processor = FixNestedJobsProcessor(
            job_id=self.job_id,
            args=self.args,
            user=self.user,
            result=self.result,
            result_file=self.result_file,
            cancel_event=self.cancel_event,
        )
        return processor.run()


# --- main pipeline --------------------------------------------
def fix_nested_jobs_worker_entry(
    *,
    job_id: str,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """Entry point for the background job."""

    worker = FixNestedJobsWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "fix_nested_jobs_worker_entry",
    "FixNestedJobsWorker",
]
