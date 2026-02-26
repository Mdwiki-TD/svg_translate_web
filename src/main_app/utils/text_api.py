"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import mwclient

logger = logging.getLogger(__name__)


def verify_required_fields(required_fields: Dict[str, Any]) -> Dict[str, bool]:
    """
    Verify that all required fields are present in the data dictionary.

    Args:
        data: The dictionary to check.
        required_fields: A list of required field names.
    Returns:

    """
    data = {}
    for field, value in required_fields.items():
        if not value:
            logger.error(f"Missing required field: {field}")
            data[field] = False
        else:
            data[field] = True
    return data


def get_file_text(
    file_name: str,
    site: mwclient.Site | None,
) -> str:
    """
    Get the wikitext of a file on Wikimedia Commons.
    Args:
        file_name: The name of the file on Commons (e.g., "File:Example.svg").
        site: Authenticated mwclient.Site object for Commons.
    Returns:
        The wikitext of the file, or an empty string if it cannot be retrieved.
    """
    if not file_name:
        logger.error("No file name provided to get_file_text")
        return ""
    if not site:
        logger.error("No site provided to get_file_text")
        return ""
    if not file_name.startswith("File:"):
        file_name = "File:" + file_name

    return ""


def update_file_text(
    original_file: str,
    updated_file_text: str,
    site: mwclient.Site | None,
) -> dict:
    """
    Update the wikitext of the original file to link to the cropped version.

    Args:
        original_file: The name of the original file on Commons.
        updated_file_text: The new wikitext for the original file.
        site: Authenticated mwclient.Site object for Commons.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str).
    """
    is_all_fields_valid = verify_required_fields({
        "original_file": original_file,
        "updated_file_text": updated_file_text,
        "site": site,
    })
    if not all(is_all_fields_valid.values()):
        unfilled_fields = [field for field, is_valid in is_all_fields_valid.items() if not is_valid]
        list_str = ", ".join(unfilled_fields)
        logger.error(f"Missing required fields for update_file_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    if not original_file.startswith("File:"):
        original_file = "File:" + original_file
