"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mwclient.client import Site

from ....api_services import upload_file

logger = logging.getLogger(__name__)


def upload_cropped_file(
    cropped_filename: str,
    cropped_path: Path,
    site: Site | None,
    wikitext: str | None = None,
) -> dict[str, Any]:
    """
    Upload cropped file to Commons with new name.

    Args:
        cropped_filename: The new filename for the cropped version (with File: prefix)
        cropped_path: Path to the cropped file
        site: Authenticated Site object for Commons
        wikitext: The wikitext content for the cropped file

    Returns:
        dict with keys: success (bool), cropped_filename (str|None), error (str|None)
    """
    result = {
        "success": False,
        "cropped_filename": cropped_filename,
        "error": None,
        "file_exists": None,
        "skipped": None,
    }

    if not site:
        result["error"] = "Failed to authenticate with Commons"
        return result

    # Get clean filename (remove File: prefix)
    clean_cropped_name = cropped_filename.removeprefix("File:")

    # Prepare upload summary
    original_file = clean_cropped_name.replace(" (cropped).svg", ".svg")
    summary = f"[[:File:{original_file}]] cropped to remove the footer."

    try:
        upload_result = upload_file(
            file_name=clean_cropped_name,
            file_path=cropped_path,
            description=wikitext,
            site=site,
            summary=summary,
            new_file=True,
        )

        if upload_result.get("result") == "Success":
            result["success"] = True
            logger.info("Successfully uploaded cropped file: %s", cropped_filename)
        else:
            error_msg = upload_result.get("error", "Unknown upload error")
            if error_msg == "File already exists on Commons":
                result["file_exists"] = True
                logger.warning("Skipped upload for %s: file already exists on Commons", cropped_filename)
            else:
                result["error"] = f"Upload failed: {error_msg}"
                logger.warning("Failed to upload %s: %s", cropped_filename, error_msg)

    except Exception as e:
        result["error"] = f"Exception during upload: {str(e)}"
        logger.exception("Error uploading %s", cropped_filename)

    return result


__all__ = [
    "upload_cropped_file",
]
