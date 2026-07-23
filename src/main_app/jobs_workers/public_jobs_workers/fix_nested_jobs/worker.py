"""
Worker module for fix_nested_jobs.
"""

from __future__ import annotations

import logging
import tempfile
import threading
from pathlib import Path
from typing import Any
from collections.abc import Callable

from mwclient.client import Site

from ....api_services import download_svg_file, get_user_site, upload_fixed_svg
from ....shared.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
    detect_nested_tags,
    fix_nested_tags,
    verify_fix,
)
from ...base_worker import BaseObjectsJobWorker
from .objects import FileResult, FixNestedJobsWorkerObject, StageDetail

logger = logging.getLogger(__name__)


class FixNestedJobsProcessor(BaseObjectsJobWorker):
    """
    Orchestrates the pipeline for fixing nested tags in SVG files.
    """

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(job_id, user, cancel_event)
        self.result: FixNestedJobsWorkerObject = FixNestedJobsWorkerObject()
        self.result.job_id = self.job_id
        self.args = args or {}
        self.result.args = self.args

        self.upload_limit = self.args.get("upload_limit") or 0

        self.filename = self.args.get("filename")
        self.site: Site | None = None

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "fix_nested_jobs"

    def _download_step(self) -> bool | None:
        """Download SVG files from Commons."""

        temp_dir = Path(tempfile.gettempdir())

        download_result = download_svg_file(self.filename, temp_dir)

        if download_result.get("ok"):
            self.result.stages.download._update("success", "Downloaded success")
            self.result.file_result = FileResult(
                success=True,
                status="success",
                path=str(download_result.get("path")),
                error=None,
            )
            return True

        self.result.stages.download._update("failed", "Downloaded Failed")

        # Update stage message
        self.result.file_result = FileResult(
            success=False,
            status="failed",
            path=None,
            error=download_result.get("error") or "download_failed",
        )

        return False

    def _analyze_step(self) -> bool | None:
        """Analyze nested tags in downloaded files."""

        if self.result.stages.download.status != "success" or not self.result.file_result.path:
            self.result.stages.analyze._update("skipped", "download step Failed")
            return None

        file_path = Path(self.result.file_result.path)
        if not file_path.is_file():
            self.result.stages.analyze._update("failed", "File not found")
            return False

        detect_result: DetectionResult = detect_nested_tags(file_path)

        self.result.file_result.nested_tags_before = detect_result.count
        self.result.file_result.nested_tags = detect_result.tags

        if detect_result.count == 0:
            self.result.stages.analyze._update("skipped", "No nested tags found")
            return None

        analyze_message = f"Found {detect_result.count} nested tags"
        self.result.stages.analyze._update("success", analyze_message)

        return True

    def _fix_step(self) -> bool | None:
        """Fix nested tags in files."""

        if self.result.stages.analyze.status != "success":
            self.result.stages.fix._update("skipped", self.result.stages.analyze.message or "skipped")
            return None

        file_path = Path(self.result.file_result.path)
        fix_success = fix_nested_tags(file_path)

        if fix_success:
            self.result.stages.fix._update("success", "Nested tags fixed successfully")
            return True

        self.result.stages.fix._update("failed", "Failed to fix nested tags")
        return False

    def _verify_step(self) -> bool | None:
        """Verify that nested tags were fixed."""

        if self.result.stages.fix.status != "success":
            self.result.stages.verify._update("skipped", "fix failed")
            return None

        file_path = Path(self.result.file_result.path)
        before_count = self.result.file_result.nested_tags_before
        verify_result: VerificationResult = verify_fix(file_path, before_count)

        self.result.file_result.nested_tags_after = verify_result.after
        self.result.file_result.nested_tags_fixed = verify_result.fixed

        if verify_result.fixed > 0:
            message = f"Verified: {verify_result.fixed} tags fixed"
            self.result.stages.verify._update("success", message)
            return True

        message = "No tags were fixed"
        self.result.stages.verify._update("failed", message)

        return False

    def _upload_step(self) -> bool | None:
        """Upload fixed files to Commons."""

        upload_enabled = self.args.get("upload", True)
        if not upload_enabled:
            self.result.stages.upload._update("skipped", "Upload disabled")
            return None

        if not self.site:
            self.result.stages.upload._update("failed", "Authentication failed")
            return None

        if self.result.stages.verify.status != "success":
            self.result.stages.upload._update("skipped", "Skipped (not fixed)")
            return None

        file_path = Path(self.result.file_result.path)
        tags_fixed = self.result.file_result.nested_tags_fixed

        upload_result = upload_fixed_svg(
            self.filename,
            file_path,
            tags_fixed,
            self.site,
        )

        if upload_result.get("ok"):
            self.result.stages.upload._update("success", "Uploaded successfully")
            return True

        message = upload_result.get("error") or "Upload failed"

        self.result.stages.upload._update("failed", message)

        return False

    def _run_stage(
        self,
        stage: StageDetail,
        step_func: Callable[[], bool | None],
    ) -> bool:
        """Run a single stage and update result."""
        stage_name = stage.name

        if self.is_cancelled():
            stage.status = "cancelled"
            return False

        stage.status = "running"
        self._save_progress()

        try:
            # Call the lambda / callback directly without passing args
            step_result = step_func()
            if step_result:
                return True
            elif step_result is False:
                self.result.status = "failed"
                return False
            else:
                self.result.status = "skipped"
                return False

        except Exception as e:
            logger.exception("Error in stage %s", stage_name)
            stage.status = "failed"
            stage.message = str(e)
            self.result.status = "failed"
            return False

    def process(self) -> FixNestedJobsWorkerObject:
        """Execute the full pipeline."""

        self.site = get_user_site(self.user)

        if not self.filename:
            logger.error("No filename found")
            self.result.status = "failed"
            return self.result

        self.result.filename = self.filename

        # ----------------------------------------------
        # Stage 1: Download SVG files

        if not self._run_stage(self.result.stages.download, self._download_step):
            return self.result

        # ----------------------------------------------
        # Stage 2: Analyze nested tags
        if not self._run_stage(self.result.stages.analyze, self._analyze_step):
            return self.result

        # ----------------------------------------------
        # Stage 3: Fix nested tags
        if not self._run_stage(self.result.stages.fix, self._fix_step):
            return self.result

        # ----------------------------------------------
        # Stage 4: Verify fixes
        if not self._run_stage(self.result.stages.verify, self._verify_step):
            return self.result

        # ----------------------------------------------
        # Stage 5: Upload fixed files

        if not self._run_stage(self.result.stages.upload, self._upload_step):
            return self.result

        return self.result


__all__ = [
    "FixNestedJobsProcessor",
]
