""" """

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from ....api_services import download_commons_file_core

logger = logging.getLogger(__name__)


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

    # Sanitize filename to prevent path traversal
    safe_name = Path(clean_filename).name
    if not safe_name or safe_name in (".", "..") or "/" in safe_name or "\\" in safe_name:
        result["error"] = "Invalid filename"
        return result

    # Determine output path - maintain original filename
    out_path = (output_dir / safe_name).resolve()

    # Verify the resolved path is within the output directory
    try:
        out_path.relative_to(output_dir.resolve())
    except ValueError:
        result["error"] = "Path traversal detected"
        logger.warning(f"Path traversal attempt detected: {clean_filename}")
        return result

    # Use the core download function
    try:
        content = download_commons_file_core(safe_name, session, timeout=60)
    except Exception as e:
        result["error"] = f"Download failed: {str(e)}"
        logger.exception(f"Failed to download {safe_name}")
        return result

    try:
        # Save the file
        out_path.write_bytes(content)
        file_size = len(content)

        result["success"] = True
        result["path"] = str(out_path.name)
        result["size_bytes"] = file_size
        logger.info(f"Downloaded: {safe_name} ({file_size} bytes)")

    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        logger.exception(f"Error saving {safe_name}")

    return result


__all__ = [
    "download_file_from_commons",
]
