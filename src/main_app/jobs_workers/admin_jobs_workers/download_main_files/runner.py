"""
Worker module for downloading main files from remote source to local filesystem.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from flask import send_file

from ....config import settings
from .worker import DownloadMainFilesWorker

# Zip file name constant
MAIN_FILES_ZIP_NAME = "main_files.zip"

logger = logging.getLogger(__name__)


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


__all__ = [
    "download_main_files_for_templates",
    "create_main_files_zip",
]
