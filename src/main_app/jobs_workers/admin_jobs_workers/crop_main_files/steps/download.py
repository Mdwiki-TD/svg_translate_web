"""
Module for handling download of main files from Wikimedia Commons for cropping.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from .....api_services.files_service.downloader import download_and_save

logger = logging.getLogger(__name__)

def download_file_for_cropping(
    filename: str,
    output_dir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """
    Download a single file from Wikimedia Commons for cropping.

    Args:
        filename: The file name (e.g., "File:Example.svg")
        output_dir: Directory where the file should be saved
        session: Optional requests session to use

    Returns:
        dict with keys: success (bool), path (Path|None), error (str|None)
    """
    result = {
        "success": False,
        "path": None,
        "error": None,
    }

    if not filename:
        result["error"] = "Empty filename"
        return result

    # Extract just the filename part (remove "File:" prefix if present)
    clean_filename = filename.removeprefix("File:")

    try:
        d_result = download_and_save(
            title=clean_filename,
            out_dir=output_dir,
            session=session,
            overwrite_download=True,
        )

        if d_result.result == "success":
            result["success"] = True
            result["path"] = Path(d_result.path)
            logger.info("Downloaded for cropping: %s", clean_filename)
        elif d_result.result == "existing":
            result["success"] = True
            result["path"] = Path(d_result.path)
            logger.info("Using existing file for cropping: %s", clean_filename)
        else:
            result["error"] = f"Download failed: {d_result.error or 'unknown'}"
            logger.warning("Failed to download %s", clean_filename)

    except Exception as e:
        result["error"] = f"Exception during download: {str(e)}"
        logger.exception("Error downloading %s", clean_filename)

    return result


__all__ = [
    "download_file_for_cropping",
]
