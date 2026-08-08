""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests

from ....api_services.files_service import download_commons_file_core

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    success: bool = False
    size_bytes: int | None = None
    path: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_download_file(
    filename: str,
    output_dir: Path,
    session: requests.Session,
) -> DownloadResult:
    """
    Download a single file from Wikimedia Commons.

    Args:
        filename: The file name (e.g., "File:Example.svg")
        output_dir: Directory where the file should be saved
        session: requests session to use
    """
    result = {
        "success": False,
        "path": None,
        "size_bytes": None,
        "error": None,
    }

    if not filename:
        return DownloadResult(error="Empty filename")

    # Extract just the filename part (remove "File:" prefix if present)
    clean_filename = filename.removeprefix("File:")

    # Determine output path - maintain original filename
    out_path = output_dir / clean_filename

    # Use the core download function
    try:
        content = download_commons_file_core(clean_filename, session, timeout=60)
    except Exception as e:
        result["error"] = f"Download failed: {str(e)}"
        logger.exception("Failed to download %s", clean_filename)
        return DownloadResult(error=f"Download failed: {str(e)}")

    try:
        # Save the file
        out_path.write_bytes(content)
        file_size = len(content)

        result["success"] = True
        result["path"] = str(out_path.name)
        result["size_bytes"] = file_size
        logger.info("Downloaded: %s (%d bytes)", clean_filename, file_size)
        return DownloadResult(success=True, path=str(out_path.name), size_bytes=file_size)

    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        logger.exception("Error saving %s", clean_filename)

        return DownloadResult(error=f"Unexpected error: {str(e)}")


def download_file_from_commons(
    filename: str,
    output_dir: Path,
    session: requests.Session,
) -> dict[str, Any]:
    """
    Download a single file from Wikimedia Commons.

    Args:
        filename: The file name (e.g., "File:Example.svg")
        output_dir: Directory where the file should be saved
        session: requests session to use

    Returns:
        dict with keys:
            - success (bool)
            - path (str|None)
            - size_bytes (int|None)
            - error (str|None)
    """
    result = run_download_file(filename, output_dir, session)
    return result.to_dict()


__all__ = [
    "download_file_from_commons",
]
