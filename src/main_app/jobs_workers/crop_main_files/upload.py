"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from ...tasks.uploads import get_user_site, upload_file

logger = logging.getLogger(__name__)


def upload_cropped_file(
    cropped_filename: str,
    cropped_path: Path,
    user: Dict[str, Any],
    wikitext: str = None,
) -> dict[str, Any]:
    """
    Upload cropped file to Commons with new name.

    Args:
        cropped_filename: The new filename for the cropped version (with File: prefix)
        cropped_path: Path to the cropped file
        user: User authentication data for OAuth uploads
        wikitext: The wikitext content for the cropped file

    Returns:
        dict with keys: success (bool), cropped_filename (str|None), error (str|None)
    """
    result = {
        "success": False,
        "cropped_filename": cropped_filename,
        "error": None,
    }

    if not user:
        result["error"] = "No user authentication provided"
        return result

    # Get clean filename (remove File: prefix)
    clean_cropped_name = cropped_filename[5:] if cropped_filename.startswith("File:") else cropped_filename

    # Get user site for upload
    site = get_user_site(user)
    if not site:
        result["error"] = "Failed to authenticate with Commons"
        return result

    # Prepare upload summary
    summary_parts = ["Cropped version of file"]
    summary = " | ".join(summary_parts)

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
            logger.info(f"Successfully uploaded cropped file: {cropped_filename}")
        else:
            error_msg = upload_result.get("error", "Unknown upload error")
            result["error"] = f"Upload failed: {error_msg}"
            logger.warning(f"Failed to upload {cropped_filename}: {error_msg}")

    except Exception as e:
        result["error"] = f"Exception during upload: {str(e)}"
        logger.exception(f"Error uploading {cropped_filename}")

    return result


__all__ = [
    "upload_cropped_file",
]
