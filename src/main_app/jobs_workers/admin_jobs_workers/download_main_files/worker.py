"""
Worker module for downloading main files from remote source to local filesystem.
"""

from __future__ import annotations

import logging
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from flask import send_file

from ....api_services import create_commons_session
from ....config import settings
from ....db.models import TemplateRecord
from ....db.services import list_templates
from ...base_worker_object import BaseObjectsJobWorker
from .download_helper import download_file_from_commons
from .objects import DownloadMainFilesWorkerObject, FileInfo

# Zip file name constant
MAIN_FILES_ZIP_NAME = "main_files.zip"

logger = logging.getLogger(__name__)


class DownloadMainFilesWorker(BaseObjectsJobWorker):
    """Worker for downloading main files from Commons to local filesystem."""

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.output_dir = Path(settings.paths.main_files_path)

        super().__init__(job_id, user, cancel_event)
        self.result: DownloadMainFilesWorkerObject = DownloadMainFilesWorkerObject()
        self.result.output_path = str(self.output_dir)
        self.session: requests.Session | None = None

        self.args = args or {}
        self.result.args = self.args
        self.limit_items = self.args.get("limit_items") or 0

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "download_main_files"

    def _apply_limits(self, templates_with_files: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(templates_with_files) > _limit:
            logger.info("Job %s: limiting from %d to %d page", self.job_id, len(templates_with_files), _limit)
            return templates_with_files[:_limit]
        return templates_with_files

    def _load_templates(self) -> list[TemplateRecord]:
        # Get all templates with main files
        templates = list_templates()
        templates_with_files = [t for t in templates if t.main_file]
        return self._apply_limits(templates_with_files)

    def _process_one_item(self, template: TemplateRecord) -> None:
        self.result.summary.processed += 1

        file_info = FileInfo(
            template_id=template.id,
            template_title=template.title,
            filename=template.main_file,
            timestamp=datetime.now().isoformat(),
        )

        # Extract just the filename part (remove "File:" prefix if present)
        clean_filename = template.main_file
        if clean_filename:
            clean_filename = clean_filename.removeprefix("File:")

        # Check if file already exists
        # out_path = self.output_dir / clean_filename
        # if out_path.exists(): self.result.summary.exists += 1

        try:
            # Download the file (will overwrite if exists)
            download_result = download_file_from_commons(
                filename=clean_filename,
                output_dir=self.output_dir,
                session=self.session,
            )

        except Exception as e:
            file_info.status = "failed"
            file_info.reason = f"Exception: {str(e)}"
            file_info.error_type = type(e).__name__
            self.result.files_failed.append(file_info.to_dict())
            self.result.summary.failed += 1
            logger.exception("Job %s: Error processing %s", self.job_id, template.title)
            return False

        # download_result = { "success": False, "path": None, "size_bytes": None, "error": None}
        if download_result.get("success"):
            file_info.status = "downloaded"
            file_info.path = download_result.get("path")
            file_info.size_bytes = download_result.get("size_bytes")
            self.result.files_downloaded.append(file_info.to_dict())
            self.result.summary.success += 1
            return True

        error = download_result.get("error")

        file_info.status = "failed"
        file_info.reason = error
        self.result.files_failed.append(file_info.to_dict())
        self.result.summary.failed += 1
        logger.warning("Job %s: Failed to download %s: %s", self.job_id, clean_filename, error)

        return False

    def process(self) -> DownloadMainFilesWorkerObject:
        """Execute the download processing logic."""
        templates_with_files = self._load_templates()

        self.result.summary.total = len(templates_with_files)
        self.result.output_path = str(self.output_dir)

        logger.info("Job %s: Found %d templates with main files", self.job_id, len(templates_with_files))

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a shared session for all downloads
        self.session = create_commons_session(settings.other.user_agent)

        per_item = self.get_priority(len(templates_with_files))

        for n, template in enumerate(templates_with_files, start=1):
            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, len(templates_with_files), template.title)

            # Check for cancellation
            if self.is_cancelled():
                logger.info("Job %s: Cancellation detected, stopping.", self.job_id)
                break

            ok = self._process_one_item(template)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            # Save progress periodically
            if n == 1 or n % per_item == 0:
                self._save_progress()

        # Generate zip file after successful completion
        if self.result.status != "cancelled":
            try:
                generate_main_files_zip()
                logger.info("Job %s: Generated main_files.zip successfully", self.job_id)
            except Exception as e:
                logger.exception("Job %s: Failed to generate main_files.zip: %s", self.job_id, e)

        logger.info(
            "Job %s completed: %d success, %d failed",
            self.job_id,
            self.result.summary.success,
            self.result.summary.failed,
        )

        return self.result


def download_main_files_for_templates(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """
    Background worker to download main files for all templates.

    Args:
        job_id: The job ID
        user: User authentication data (not used for downloads, but kept for consistency)
        cancel_event: Optional event to check for cancellation
        args: Optional arguments dict (unused, for unified signature)
    """
    logger.info("Starting job %s: download main files for templates", job_id)

    worker = DownloadMainFilesWorker(job_id, user, cancel_event, args)
    worker.run()


def generate_main_files_zip() -> Path:
    """
    Generate a zip archive of all files in the main_files_path directory.

    Creates the zip file on disk in the main_files_path directory.
    Only includes actual files (not directories), excluding the zip file itself.

    Returns:
        Path: Path to the created zip file

    Raises:
        FileNotFoundError: If main_files_path directory does not exist
        RuntimeError: If no files are found to zip
    """
    main_files_path = Path(settings.paths.main_files_path)

    if not main_files_path.exists():
        raise FileNotFoundError(f"Main files directory does not exist: {main_files_path}")

    zip_file_path = main_files_path / MAIN_FILES_ZIP_NAME

    # Create the zip file
    file_count = 0
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in main_files_path.iterdir():
            if file_path.is_file() and file_path.name != MAIN_FILES_ZIP_NAME:
                zip_file.write(file_path, file_path.name)
                file_count += 1

    if file_count == 0:
        # Remove empty zip file and raise error
        zip_file_path.unlink(missing_ok=True)
        raise RuntimeError("No files found to zip in main_files_path")

    logger.info("Generated %s with %d files", zip_file_path, file_count)
    return zip_file_path


def create_main_files_zip() -> tuple[Any, int]:
    """
    Serve the main files zip archive.

    Checks for an existing zip file first. If it doesn't exist, returns an error.
    The zip file should be generated automatically when a download job completes successfully.

    Returns:
        tuple: (send_file response or error message, status_code)
    """
    main_files_path = Path(settings.paths.main_files_path)
    zip_file_path = main_files_path / MAIN_FILES_ZIP_NAME

    if not main_files_path.exists():
        return "Main files directory does not exist", 404

    # Check if zip file exists
    if not zip_file_path.exists():
        return ("Zip file not found. Please run a 'Download Main Files' job first to generate the archive.", 404)

    # Check if zip file is valid (not empty)
    if zip_file_path.stat().st_size == 0:
        return "Zip file is empty or corrupted. Please re-run the 'Download Main Files' job.", 500

    return (
        send_file(zip_file_path, mimetype="application/zip", as_attachment=True, download_name=MAIN_FILES_ZIP_NAME),
        200,
    )


__all__ = [
    "download_main_files_for_templates",
    "DownloadMainFilesWorker",
    "create_main_files_zip",
    "generate_main_files_zip",
    "MAIN_FILES_ZIP_NAME",
]
