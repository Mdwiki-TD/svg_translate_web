"""
Processor for fix_nested_jobs.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import mwclient
import requests

from ...api_services.clients import create_commons_session, get_user_site
from ...config import settings
from ...services import jobs_service
from ...shared.fix_nested.worker import (
    detect_nested_tags,
    download_svg_file,
    fix_nested_tags,
    upload_fixed_svg,
    verify_fix,
)

logger = logging.getLogger(__name__)


@dataclass
class FixNestedJobsProcessor:
    """
    Orchestrates the pipeline for fixing nested tags in SVG files.
    """

    task_id: str | int
    args: Any
    user: dict[str, Any] | None
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
            jobs_service.save_job_result_by_name(self.result_file, self.result)
        except Exception:
            logger.exception(f"Job {self.task_id}: Failed to save progress")

    def _is_cancelled(self, stage_name: str | None = None) -> bool:
        cancelled = False
        if self.cancel_event and self.cancel_event.is_set():
            cancelled = True
        elif jobs_service.is_job_cancelled(self.task_id, job_type="fix_nested_jobs"):
            cancelled = True

        if cancelled:
            self.result["status"] = "cancelled"
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

        self.session = create_commons_session(settings.oauth.user_agent)
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

        upload_enabled = self.args.get("upload", True)
        if not upload_enabled:
            self._update_step("upload", "Skipped", "Upload disabled")
        elif not self.site:
            self._update_step("upload", "Failed", "Authentication failed")
            self.result["status"] = "Failed"
        else:
            if not self._run_stage("upload", self._upload_step):
                return self.result

        # ----------------------------------------------
        # Finalize
        self.result["status"] = "completed"
        self.result["completed_at"] = datetime.now().isoformat()
        self._save_progress()

        return self.result

    def _download_step(self) -> dict[str, Any]:
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
            return {"success": True, "message": "Downloaded success"}

        self._update_step("download", "Failed", "Downloaded Failed")

        # Update stage message
        self.result["file_result"] = {
            "success": False,
            "status": "Failed",
            "path": None,
            "error": download_result.get("error", "download_failed"),
        }

        return {"success": False, "message": "Downloaded Failed"}

    def _analyze_step(self) -> dict[str, Any]:
        """Analyze nested tags in downloaded files."""

        if self.result["stages"]["download"]["status"] != "success" or not self.result["file_result"].get("path"):
            return False

        file_path = Path(self.result["file_result"]["path"])
        if not file_path.is_file():
            self._update_step("analyze", "Failed", "File not found")
            return {"success": False, "error": "File not found"}

        detect_result = detect_nested_tags(file_path)

        self.result["file_result"]["nested_tags_before"] = detect_result["count"]
        self.result["file_result"]["nested_tags"] = detect_result["tags"]

        if detect_result["count"] == 0:
            self._update_step("analyze", "skipped", "No nested tags found")
            return {"success": None, "message": "No nested tags found"}

        analyze_message = f"Found {detect_result['count']} nested tags"
        self._update_step("analyze", "success", analyze_message)

        return {
            "success": True,
            "message": analyze_message,
        }

    def _fix_step(self) -> dict[str, Any]:
        """Fix nested tags in files."""

        if self.result["stages"]["analyze"]["status"] != "success":
            self._update_step("fix", "skipped", self.result["stages"]["analyze"]["message"] or "Skipped")
            return {"success": None, "error": "analyze failed"}

        file_path = Path(self.result["file_result"]["path"])
        fix_success = fix_nested_tags(file_path)

        if fix_success:
            self._update_step("fix", "success", "Fixed True")
            return {"success": True, "message": "Fixed True"}

        self._update_step("fix", "Failed", "Failed to fix nested tags")
        return {"success": False, "message": "Fixed failed"}

    def _verify_step(self) -> dict[str, Any]:
        """Verify that nested tags were fixed."""

        if self.result["stages"]["fix"]["status"] != "success":
            self._update_step("verify", "skipped", "fix failed")
            return {"success": False, "error": "fix failed"}

        file_path = Path(self.result["file_result"]["path"])
        before_count = self.result["file_result"].get("nested_tags_before", 0)
        verify_result = verify_fix(file_path, before_count)

        self.result["file_result"]["nested_tags_after"] = verify_result["after"]
        self.result["file_result"]["nested_tags_fixed"] = verify_result["fixed"]

        if verify_result["fixed"] > 0:
            message = f"Verified: {verify_result['fixed']} tags fixed"
            self._update_step("verify", "success", message)
            return {"success": True, "message": message}

        message = "No tags were fixed"
        self._update_step("verify", "Failed", message)

        return {"success": False, "error": message}

    def _upload_step(self) -> dict[str, Any]:
        """Upload fixed files to Commons."""

        if self.result["stages"]["verify"]["status"] != "success":
            self._update_step("upload", "skipped", "Skipped (not fixed)")
            return {"success": False, "error": "Skipped (not fixed)"}

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
            return {"success": True, "message": "Uploaded successfully"}

        message = upload_result.get("error", "Upload failed")

        self._update_step("upload", "Failed", message)

        return {
            "success": False,
            "error": message,
            "message": message,
        }

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
            if step_result.get("success"):
                stage["status"] = "Completed"
                stage["message"] = step_result.get("message", "")
                stage.update(step_result)
                return True
            else:
                status = "Failed" if step_result.get("success") is False else "skipped"
                stage["status"] = status
                stage["message"] = step_result.get("error", "Unknown error")
                stage.update(step_result)
                self.result["status"] = status
                return False

        except Exception as e:
            logger.exception(f"Error in stage {stage_name}")
            stage["status"] = "Failed"
            stage["message"] = str(e)
            self.result["status"] = "Failed"
            return False
