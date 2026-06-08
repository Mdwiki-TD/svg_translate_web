"""
Worker module for downloading main files from remote source to local filesystem.
"""

from __future__ import annotations

import logging
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests
from flask import send_file

from ...api_services.clients import create_commons_session, download_commons_file_core
from ...config import settings
from ...db.models import TemplateRecord
from ...db.services import list_templates
from ..base_worker import BaseJobWorker

# Zip file name constant
MAIN_FILES_ZIP_NAME = "main_files.zip"

logger = logging.getLogger(__name__)


def download_all_main_files(): ...


def download_file_from_commons(
    filename: str,
    output_dir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    Download a single file from Wikimedia Commons.

    Args:
        filename: The file name (e.g., "File:Example.svg")
        output_dir: Directory where the file should be saved
        session: Optional requests session to use

    Returns:
        dict with keys:
            - success (bool)
            - path (str|None)
            - size_bytes (int|None)
            - error (str|None)
    """
    result = {
        "success": False,
        "path": None,
        "size_bytes": None,
        "error": None,
    }

    if not filename:
        result["error"] = "Empty filename"
        return result

    # Extract just the filename part (remove "File:" prefix if present)
    clean_filename = filename.removeprefix("File:")

    # Determine output path - maintain original filename
    out_path = output_dir / clean_filename

    # Create session if not provided
    if session is None:
        session = create_commons_session(settings.other.user_agent)

    # Use the core download function
    try:
        content = download_commons_file_core(clean_filename, session, timeout=60)
    except Exception as e:
        result["error"] = f"Download failed: {str(e)}"
        logger.exception(f"Failed to download {clean_filename}")
        return result

    try:
        # Save the file
        out_path.write_bytes(content)
        file_size = len(content)

        result["success"] = True
        result["path"] = str(out_path.name)
        result["size_bytes"] = file_size
        logger.info(f"Downloaded: {clean_filename} ({file_size} bytes)")

    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        logger.exception(f"Error saving {clean_filename}")

    return result


class DownloadMainFilesWorker(BaseJobWorker):
    """Worker for downloading main files from Commons to local filesystem."""

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.output_dir = Path(settings.paths.main_files_path)
        self.limit_items = args.get("limit_items") if args else 0

        super().__init__(job_id, user, cancel_event)
        self.result: Dict[str, Any] = self.get_initial_result()
        self.session: requests.Session = None

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "download_main_files"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "status": "pending",
            "errors": [{"error": "", "error_type": ""}],
            "args": {},
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "total": 0,
                "processed": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
            },
            "output_path": str(self.output_dir),
            "files_downloaded": [],
            "files_failed": [],
        }

    def _apply_limits(self, templates_with_files: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(templates_with_files) > _limit:
            logger.info(f"Job {self.job_id}: limiting from {len(templates_with_files)} to {_limit} page")
            return templates_with_files[:_limit]
        return templates_with_files

    def _load_templates(self) -> list[TemplateRecord]:
        # Get all templates with main files
        templates = list_templates()
        templates_with_files = [t for t in templates if t.main_file]
        return self._apply_limits(templates_with_files)

    def _process_template(self, template) -> None:
        self.result["summary"]["processed"] += 1

        file_info = {
            "template_id": template.id,
            "template_title": template.title,
            "filename": template.main_file,
            "timestamp": datetime.now().isoformat(),
        }

        # Extract just the filename part (remove "File:" prefix if present)
        clean_filename = template.main_file
        clean_filename = clean_filename.removeprefix("File:")

        # Check if file already exists
        # out_path = self.output_dir / clean_filename
        # if out_path.exists(): self.result["summary"]["exists"] += 1

        try:
            # Download the file (will overwrite if exists)
            download_result = download_file_from_commons(
                clean_filename,
                self.output_dir,
                session=self.session,
            )

        except Exception as e:
            file_info["status"] = "failed"
            file_info["reason"] = f"Exception: {str(e)}"
            file_info["error_type"] = type(e).__name__
            self.result["files_failed"].append(file_info)
            self.result["summary"]["failed"] += 1
            logger.exception(f"Job {self.job_id}: Error processing {template.title}")
            return False

        # download_result = { "success": False, "path": None, "size_bytes": None, "error": None}
        if download_result.get("success"):
            file_info["status"] = "downloaded"
            file_info["path"] = download_result.get("path")
            file_info["size_bytes"] = download_result.get("size_bytes")
            self.result["files_downloaded"].append(file_info)
            self.result["summary"]["success"] += 1
            return True

        error = download_result.get("error")

        file_info["status"] = "failed"
        file_info["reason"] = error
        self.result["files_failed"].append(file_info)
        self.result["summary"]["failed"] += 1
        logger.warning(f"Job {self.job_id}: Failed to download {clean_filename}: {error}")

        return False

    def process(self) -> Dict[str, Any]:
        """Execute the download processing logic."""
        templates_with_files = self._load_templates()

        self.result["summary"]["total"] = len(templates_with_files)
        self.result["output_path"] = str(self.output_dir)

        logger.info(f"Job {self.job_id}: Found {len(templates_with_files)} templates with main files")

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a shared session for all downloads
        self.session = create_commons_session(settings.other.user_agent)

        per_item = self.get_priority(len(templates_with_files))

        for n, template in enumerate(templates_with_files, start=1):

            logger.info(f"Job {self.job_id}: Processing {n}/{len(templates_with_files)}: {template.title}")

            # Check for cancellation
            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                break

            self.result["summary"]["processed"] += 1

            ok = self._process_template(template)

            if ok and self.check_cancel_db_periodic():
                logger.info(f"Job {self.job_id}: Cancelled due to periodic check")
                return False

            # Save progress periodically
            if n == 1 or n % per_item == 0:
                self._save_progress()

        # Generate zip file after successful completion
        if self.result.get("status") != "cancelled":
            try:
                generate_main_files_zip()
                logger.info(f"Job {self.job_id}: Generated main_files.zip successfully")
            except Exception as e:
                logger.exception(f"Job {self.job_id}: Failed to generate main_files.zip: {e}")

        logger.info(
            f"Job {self.job_id} completed: "
            f"{self.result['summary']['success']} success, "
            f"{self.result['summary']['failed']} failed"
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
    logger.info(f"Starting job {job_id}: download main files for templates")

    if args and args.get("download_main_files_limit_items"):
        args.update({"limit_items": args.get("download_main_files_limit_items")})

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

    logger.info(f"Generated {zip_file_path} with {file_count} files")
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
