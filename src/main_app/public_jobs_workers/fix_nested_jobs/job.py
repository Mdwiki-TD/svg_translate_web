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

    def run(self) -> dict[str, Any]:
        """Execute the full pipeline."""
        self.result["status"] = "running"
        self._save_progress()

        self.session = create_commons_session(settings.oauth.user_agent)
        self.site = get_user_site(self.user)

        if not self.filename:
            logger.error("No filename found")
            self.result["status"] = "failed"
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
            self.result["stages"]["upload"]["status"] = "Skipped"
            self.result["stages"]["upload"]["message"] = "Upload disabled"
        elif not self.site:
            self.result["stages"]["upload"]["status"] = "Failed"
            self.result["stages"]["upload"]["message"] = "Authentication failed"
            self.result["status"] = "failed"
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

        file_result = {
            "status": "pending",
            "path": None,
            "error": None,
        }

        if download_result["ok"]:
            file_result["status"] = "success"
            file_result["path"] = str(download_result["path"])
        else:
            file_result["status"] = "failed"
            file_result["error"] = download_result.get("error", "download_failed")

        # Update stage message
        self.result["file_result"] = file_result
        self.result["stages"]["download"]["message"] = "Downloaded 1/1"

        return {
            "success": True,
            "message": "Downloaded True",
        }

    def _analyze_step(self) -> dict[str, Any]:
        """Analyze nested tags in downloaded files."""

        if self.result["file_result"]["status"] != "success" or not self.result["file_result"].get("path"):
            return False

        file_path = Path(self.result["file_result"]["path"])
        if not file_path.is_file():
            self.result["file_result"]["analyze_status"] = "failed"
            return {"success": False, "error": "File not found"}

        detect_result = detect_nested_tags(file_path)

        self.result["file_result"]["nested_tags_before"] = detect_result["count"]
        self.result["file_result"]["nested_tags"] = detect_result["tags"]

        if detect_result["count"] == 0:
            self.result["file_result"]["analyze_status"] = "skipped"
            self.result["file_result"]["analyze_message"] = "No nested tags found"
            return {"success": None, "message": "No nested tags found"}

        self.result["file_result"]["analyze_status"] = "success"
        self.result["file_result"]["analyze_message"] = f"Found {detect_result['count']} nested tags"

        self.result["stages"]["analyze"]["message"] = f"Found {detect_result['count']} nested tags"

        return {
            "success": True,
            "message": self.result["file_result"]["analyze_message"],
        }

    def _fix_step(self) -> dict[str, Any]:
        """Fix nested tags in files."""

        if self.result["file_result"].get("analyze_status") != "success":
            self.result["file_result"]["fix_status"] = "skipped"
            self.result["file_result"]["fix_message"] = self.result["file_result"].get("analyze_message", "Skipped")
            return {"success": None, "error": "analyze failed"}

        file_path = Path(self.result["file_result"]["path"])
        fix_success = fix_nested_tags(file_path)

        if fix_success:
            self.result["file_result"]["fix_status"] = "success"
            self.result["file_result"]["fix_message"] = "Fixed nested tags"
            self.result["stages"]["fix"]["message"] = "Fixed True"

            return {"success": True, "message": "Fixed True"}

        self.result["file_result"]["fix_status"] = "failed"
        self.result["file_result"]["fix_message"] = "Failed to fix nested tags"
        return {"success": False, "message": "Fixed failed"}

    def _verify_step(self) -> dict[str, Any]:
        """Verify that nested tags were fixed."""

        if self.result["file_result"].get("fix_status") != "success":
            self.result["file_result"]["verify_status"] = "skipped"
            return {"success": False, "error": "fix failed"}

        file_path = Path(self.result["file_result"]["path"])
        before_count = self.result["file_result"].get("nested_tags_before", 0)
        verify_result = verify_fix(file_path, before_count)

        self.result["file_result"]["nested_tags_after"] = verify_result["after"]
        self.result["file_result"]["nested_tags_fixed"] = verify_result["fixed"]

        if verify_result["fixed"] > 0:
            self.result["file_result"]["verify_status"] = "success"
            self.result["file_result"]["verify_message"] = f"Verified: {verify_result['fixed']} tags fixed"
        else:
            self.result["file_result"]["verify_status"] = "failed"
            self.result["file_result"]["verify_message"] = "No tags were fixed"

        self.result["stages"]["verify"]["message"] = "Verified True"

        return {
            "success": True,
            "message": "Verified True",
        }

    def _upload_step(self) -> dict[str, Any]:
        """Upload fixed files to Commons."""

        if self.result["file_result"].get("verify_status") != "success":
            self.result["file_result"]["upload_status"] = "skipped"
            self.result["file_result"]["upload_message"] = "Skipped (not fixed)"
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
            self.result["file_result"]["upload_status"] = "success"
            self.result["file_result"]["upload_message"] = "Uploaded successfully"
            self.result["file_result"]["upload_result"] = upload_result.get("result")
        else:
            self.result["file_result"]["upload_status"] = "failed"
            self.result["file_result"]["upload_message"] = upload_result.get("error", "Upload failed")

        self.result["stages"]["upload"]["message"] = "Uploaded True"

        return {
            "success": True,
            "message": "Uploaded True",
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
                stage["status"] = "Failed" if step_result.get("success") is False else "skipped"
                stage["message"] = step_result.get("error", "Unknown error")
                stage.update(step_result)
                self.result["status"] = "failed"
                return False

        except Exception as e:
            logger.exception(f"Error in stage {stage_name}")
            stage["status"] = "Failed"
            stage["message"] = str(e)
            self.result["status"] = "failed"
            return False
