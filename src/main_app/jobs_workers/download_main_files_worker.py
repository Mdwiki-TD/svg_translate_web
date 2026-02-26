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

from ..db.db_Templates import TemplatesDB
from ..config import settings
from ..utils.commons_client import create_commons_session, download_commons_file_core
from .base_worker import BaseJobWorker

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
        dict with keys: success (bool), path (str|None), size_bytes (int|None), error (str|None)
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
    clean_filename = filename[5:] if filename.startswith("File:") else filename

    # Determine output path - maintain original filename
    out_path = output_dir / clean_filename

    # Create session if not provided
    if session is None:
        session = create_commons_session(settings.oauth.user_agent)

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
        user: Dict[str, Any] | None = None,
        cancel_event: threading.Event | None = None,
    ):
        self.output_dir = Path(settings.paths.main_files_path)
        super().__init__(job_id, user, cancel_event)

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "download_main_files"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "output_path": str(self.output_dir),
            "files_downloaded": [],
            "files_failed": [],
            "summary": {
                "total": 0,
                "downloaded": 0,
                "failed": 0,
                "exists": 0,
            },
        }

    def process(self) -> Dict[str, Any]:
        """Execute the download processing logic."""
        from . import jobs_service

        result = self.result

        # Get all templates with main files
        templates_db = TemplatesDB(settings.database_data, use_bg_engine=True)
        templates = templates_db.list()
        templates_with_files = [t for t in templates if t.main_file]

        # Apply development mode limit from settings
        dev_limit = settings.download.dev_limit
        if dev_limit > 0 and len(templates_with_files) > dev_limit:
            logger.info(
                f"Job {self.job_id}: Development mode - limiting download from "
                f"{len(templates_with_files)} to {dev_limit} files"
            )
            templates_with_files = templates_with_files[:dev_limit]

        result["summary"]["total"] = len(templates_with_files)
        result["output_path"] = str(self.output_dir)

        logger.info(f"Job {self.job_id}: Found {len(templates_with_files)} templates with main files")

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a shared session for all downloads
        session = create_commons_session(settings.oauth.user_agent)

        for n, template in enumerate(templates_with_files, start=1):
            # Check for cancellation
            if self.is_cancelled():
                logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
                break

            # Save progress periodically
            if n == 1 or n % 10 == 0:
                try:
                    jobs_service.save_job_result_by_name(self.result_file, result)
                except Exception:
                    logger.exception(f"Job {self.job_id}: Failed to save progress")

            logger.info(f"Job {self.job_id}: Processing {n}/{len(templates_with_files)}: {template.title}")

            file_info = {
                "template_id": template.id,
                "template_title": template.title,
                "filename": template.main_file,
                "timestamp": datetime.now().isoformat(),
            }

            # Extract just the filename part (remove "File:" prefix if present)
            clean_filename = template.main_file
            if clean_filename.startswith("File:"):
                clean_filename = clean_filename[5:]

            try:
                # Check if the file already exists
                if (self.output_dir / clean_filename).exists():
                    result["summary"]["exists"] += 1

                # Download the file (will overwrite if exists)
                download_result = download_file_from_commons(
                    clean_filename,
                    self.output_dir,
                    session=session,
                )

                if download_result["success"]:
                    file_info["status"] = "downloaded"
                    file_info["path"] = download_result["path"]
                    file_info["size_bytes"] = download_result["size_bytes"]
                    result["files_downloaded"].append(file_info)
                    result["summary"]["downloaded"] += 1
                else:
                    file_info["status"] = "failed"
                    file_info["reason"] = download_result["error"]
                    result["files_failed"].append(file_info)
                    result["summary"]["failed"] += 1
                    logger.warning(
                        f"Job {self.job_id}: Failed to download {clean_filename}: {download_result['error']}"
                    )

            except Exception as e:
                file_info["status"] = "failed"
                file_info["reason"] = f"Exception: {str(e)}"
                file_info["error_type"] = type(e).__name__
                result["files_failed"].append(file_info)
                result["summary"]["failed"] += 1
                logger.exception(f"Job {self.job_id}: Error processing {template.title}")

        # Final save
        result["completed_at"] = datetime.now().isoformat()

        # Generate zip file after successful completion
        if result.get("status") != "cancelled":
            try:
                generate_main_files_zip()
                logger.info(f"Job {self.job_id}: Generated main_files.zip successfully")
            except Exception as e:
                logger.exception(f"Job {self.job_id}: Failed to generate main_files.zip: {e}")

        logger.info(
            f"Job {self.job_id} completed: "
            f"{result['summary']['downloaded']} downloaded, "
            f"{result['summary']['failed']} failed"
        )

        return result


def download_main_files_for_templates(
    job_id: int,
    user: Dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Background worker to download main files for all templates.

    This function:
    1. Fetches all templates from the database
    2. For each template with a main_file:
       - Downloads the file from Commons
       - Saves it to settings.paths.main_files_path
    3. Saves a detailed report to a JSON file

    Args:
        job_id: The job ID
        user: User authentication data (not used for downloads, but kept for consistency)
        cancel_event: Optional event to check for cancellation
    """
    logger.info(f"Starting job {job_id}: download main files for templates")
    worker = DownloadMainFilesWorker(job_id, user, cancel_event)
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
