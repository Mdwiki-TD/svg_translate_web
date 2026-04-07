"""
Processor for fix_nested_tasks.
"""

from __future__ import annotations

import logging
import re
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
from ...app_routes.fix_nested.worker import (
    detect_nested_tags,
    download_svg_file,
    fix_nested_tags,
    upload_fixed_svg,
    verify_fix,
)

logger = logging.getLogger(__name__)


@dataclass
class FixNestedTasksProcessor:
    """
    Orchestrates the pipeline for fixing nested tags in SVG files.
    """

    task_id: str | int
    title: str
    args: Any
    user: dict[str, Any] | None
    result: dict[str, Any]
    result_file: str
    cancel_event: threading.Event | None = None

    site: mwclient.Site | None = field(init=False, default=None)
    session: requests.Session | None = field(init=False, default=None)
    output_dir: Path = field(init=False)

    filenames: list[str] = field(init=False, default_factory=list)

    def __post_init__(self) -> None:
        self.output_dir = self._compute_output_dir(self.title)

    def _compute_output_dir(self, title: str) -> Path:
        name = Path(title).name
        slug = re.sub(r"[^A-Za-z0-9._\- ]+", "_", str(name)).strip("._") or "untitled"
        slug = slug.replace(" ", "_").lower()
        out = Path(settings.paths.svg_data) / "fix_nested" / slug
        out.mkdir(parents=True, exist_ok=True)

        return out

    def _save_progress(self) -> None:
        try:
            jobs_service.save_job_result_by_name(self.result_file, self.result)
        except Exception:
            logger.exception(f"Job {self.task_id}: Failed to save progress")

    def _is_cancelled(self, stage_name: str | None = None) -> bool:
        cancelled = False
        if self.cancel_event and self.cancel_event.is_set():
            cancelled = True
        elif jobs_service.is_job_cancelled(self.task_id, job_type="fix_nested_tasks"):
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

        # Parse filenames from args
        self.filenames = self._parse_filenames()
        self.result["summary"]["total"] = len(self.filenames)

        # ----------------------------------------------
        # Stage 1: Download SVG files
        def download_run_after() -> None:
            pass

        if not self._run_stage(
            "download",
            self._download_step,
            download_run_after,
        ):
            return self.result

        # ----------------------------------------------
        # Stage 2: Analyze nested tags
        def analyze_run_after() -> None:
            pass

        if not self._run_stage(
            "analyze",
            self._analyze_step,
            analyze_run_after,
        ):
            return self.result

        # ----------------------------------------------
        # Stage 3: Fix nested tags
        def fix_run_after() -> None:
            pass

        if not self._run_stage(
            "fix",
            self._fix_step,
            fix_run_after,
        ):
            return self.result

        # ----------------------------------------------
        # Stage 4: Verify fixes
        def verify_run_after() -> None:
            pass

        if not self._run_stage(
            "verify",
            self._verify_step,
            verify_run_after,
        ):
            return self.result

        # ----------------------------------------------
        # Stage 5: Upload fixed files
        def upload_run_after() -> None:
            pass

        upload_enabled = self.args.get("upload", True)
        if not upload_enabled:
            self.result["stages"]["upload"]["status"] = "Skipped"
            self.result["stages"]["upload"]["message"] = "Upload disabled"
        elif not self.site:
            self.result["stages"]["upload"]["status"] = "Failed"
            self.result["stages"]["upload"]["message"] = "Authentication failed"
            self.result["status"] = "failed"
        else:
            if not self._run_stage(
                "upload",
                self._upload_step,
                upload_run_after,
            ):
                return self.result

        # ----------------------------------------------
        # Finalize
        self.result["status"] = "completed"
        self.result["completed_at"] = datetime.now().isoformat()
        self._save_progress()

        return self.result

    def _parse_filenames(self) -> list[str]:
        """Parse filenames from args."""
        filenames = []
        # Support single filename or list
        if isinstance(self.args.get("filename"), str):
            filenames.append(self.args["filename"])
        elif isinstance(self.args.get("filename"), list):
            filenames = self.args["filename"]
        elif isinstance(self.args.get("filenames"), list):
            filenames = self.args["filenames"]
        elif isinstance(self.args.get("filenames"), str):
            # Comma-separated string
            filenames = [f.strip() for f in self.args["filenames"].split(",") if f.strip()]

        # Clean up filenames (remove File: prefix if present)
        cleaned = []
        for fn in filenames:
            if fn.lower().startswith("file:"):
                cleaned.append(fn[5:].lstrip())
            else:
                cleaned.append(fn)

        return cleaned

    def _download_step(self) -> dict[str, Any]:
        """Download SVG files from Commons."""
        results = []
        success_count = 0
        failed_count = 0

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_dir = Path(tmp_dir)

            for i, filename in enumerate(self.filenames):
                if self._is_cancelled("download"):
                    break

                download_result = download_svg_file(filename, temp_dir)

                file_result = {
                    "filename": filename,
                    "status": "pending",
                    "path": None,
                    "error": None,
                }

                if download_result["ok"]:
                    file_result["status"] = "success"
                    file_result["path"] = str(download_result["path"])
                    success_count += 1
                else:
                    file_result["status"] = "failed"
                    file_result["error"] = download_result.get("error", "download_failed")
                    failed_count += 1

                results.append(file_result)
                self.result["results"].append(file_result)

                # Update stage message
                self.result["stages"]["download"]["message"] = f"Downloaded {i + 1}/{len(self.filenames)}"
                self._save_progress()

        return {
            "success": True,
            "message": f"Downloaded {success_count}/{len(self.filenames)} files",
            "summary": {"success": success_count, "failed": failed_count},
            "results": results,
        }

    def _analyze_step(self) -> dict[str, Any]:
        """Analyze nested tags in downloaded files."""
        results = []
        success_count = 0
        skipped_count = 0

        for file_result in self.result["results"]:
            if self._is_cancelled("analyze"):
                break

            if file_result["status"] != "success" or not file_result.get("path"):
                continue

            file_path = Path(file_result["path"])
            detect_result = detect_nested_tags(file_path)

            file_result["nested_tags_before"] = detect_result["count"]
            file_result["nested_tags"] = detect_result["tags"]

            if detect_result["count"] == 0:
                file_result["analyze_status"] = "skipped"
                file_result["analyze_message"] = "No nested tags found"
                skipped_count += 1
            else:
                file_result["analyze_status"] = "success"
                file_result["analyze_message"] = f"Found {detect_result['count']} nested tags"
                success_count += 1

            results.append({
                "filename": file_result["filename"],
                "nested_count": detect_result["count"],
            })

            self.result["stages"]["analyze"]["message"] = f"Analyzed {file_result['filename']}"
            self._save_progress()

        return {
            "success": True,
            "message": f"Analyzed {len(self.result['results'])} files",
            "summary": {"analyzed": success_count, "skipped": skipped_count},
            "results": results,
        }

    def _fix_step(self) -> dict[str, Any]:
        """Fix nested tags in files."""
        success_count = 0
        failed_count = 0
        skipped_count = 0

        for file_result in self.result["results"]:
            if self._is_cancelled("fix"):
                break

            if file_result.get("analyze_status") != "success":
                file_result["fix_status"] = "skipped"
                file_result["fix_message"] = file_result.get("analyze_message", "Skipped")
                skipped_count += 1
                continue

            file_path = Path(file_result["path"])
            fix_success = fix_nested_tags(file_path)

            if fix_success:
                file_result["fix_status"] = "success"
                file_result["fix_message"] = "Fixed nested tags"
                success_count += 1
            else:
                file_result["fix_status"] = "failed"
                file_result["fix_message"] = "Failed to fix nested tags"
                failed_count += 1

            self.result["stages"]["fix"]["message"] = f"Fixed {file_result['filename']}"
            self._save_progress()

        return {
            "success": True,
            "message": f"Fixed {success_count} files",
            "summary": {"success": success_count, "failed": failed_count, "skipped": skipped_count},
        }

    def _verify_step(self) -> dict[str, Any]:
        """Verify that nested tags were fixed."""
        success_count = 0
        failed_count = 0

        for file_result in self.result["results"]:
            if self._is_cancelled("verify"):
                break

            if file_result.get("fix_status") != "success":
                file_result["verify_status"] = "skipped"
                continue

            file_path = Path(file_result["path"])
            before_count = file_result.get("nested_tags_before", 0)
            verify_result = verify_fix(file_path, before_count)

            file_result["nested_tags_after"] = verify_result["after"]
            file_result["nested_tags_fixed"] = verify_result["fixed"]

            if verify_result["fixed"] > 0:
                file_result["verify_status"] = "success"
                file_result["verify_message"] = f"Verified: {verify_result['fixed']} tags fixed"
                success_count += 1
            else:
                file_result["verify_status"] = "failed"
                file_result["verify_message"] = "No tags were fixed"
                failed_count += 1

            self.result["stages"]["verify"]["message"] = f"Verified {file_result['filename']}"
            self._save_progress()

        return {
            "success": True,
            "message": f"Verified {success_count} files",
            "summary": {"success": success_count, "failed": failed_count},
        }

    def _upload_step(self) -> dict[str, Any]:
        """Upload fixed files to Commons."""
        success_count = 0
        failed_count = 0

        for file_result in self.result["results"]:
            if self._is_cancelled("upload"):
                break

            if file_result.get("verify_status") != "success":
                file_result["upload_status"] = "skipped"
                file_result["upload_message"] = "Skipped (not fixed)"
                continue

            file_path = Path(file_result["path"])
            tags_fixed = file_result.get("nested_tags_fixed", 0)

            upload_result = upload_fixed_svg(
                file_result["filename"],
                file_path,
                tags_fixed,
                self.user,
            )

            if upload_result["ok"]:
                file_result["upload_status"] = "success"
                file_result["upload_message"] = "Uploaded successfully"
                file_result["upload_result"] = upload_result.get("result")
                success_count += 1
            else:
                file_result["upload_status"] = "failed"
                file_result["upload_message"] = upload_result.get("error", "Upload failed")
                failed_count += 1

            self.result["stages"]["upload"]["message"] = f"Uploaded {file_result['filename']}"
            self._save_progress()

        return {
            "success": True,
            "message": f"Uploaded {success_count} files",
            "summary": {"success": success_count, "failed": failed_count},
        }

    def _run_stage(
        self,
        stage_name: str,
        step_func: Any,
        run_after_func: Any | None = None,
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
                stage["data"] = step_result
                if run_after_func:
                    run_after_func()
                return True
            else:
                stage["status"] = "Failed"
                stage["message"] = step_result.get("error", "Unknown error")
                self.result["status"] = "failed"
                return False

        except Exception as e:
            logger.exception(f"Error in stage {stage_name}")
            stage["status"] = "Failed"
            stage["message"] = str(e)
            self.result["status"] = "failed"
            return False
