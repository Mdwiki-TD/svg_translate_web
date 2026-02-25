"""
Module for handling download of main files from Wikimedia Commons for cropping.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from ...tasks.downloads.download_file_utils import download_one_file

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
    clean_filename = filename[5:] if filename.startswith("File:") else filename

    # Use download_one_file from tasks.downloads
    try:
        download_result = download_one_file(
            title=clean_filename,
            out_dir=output_dir,
            i=1,
            session=session,
            overwrite=True,
        )

        if download_result["result"] == "success":
            result["success"] = True
            result["path"] = Path(download_result["path"])
            logger.info(f"Downloaded for cropping: {clean_filename}")
        elif download_result["result"] == "existing":
            result["success"] = True
            result["path"] = Path(download_result["path"])
            logger.info(f"Using existing file for cropping: {clean_filename}")
        else:
            result["error"] = f"Download failed: {download_result.get('result', 'unknown')}"
            logger.warning(f"Failed to download {clean_filename}")

    except Exception as e:
        result["error"] = f"Exception during download: {str(e)}"
        logger.exception(f"Error downloading {clean_filename}")

    return result


__all__ = [
    "download_file_for_cropping",
]
