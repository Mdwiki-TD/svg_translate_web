"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
import mwclient

from .text_utils import ensure_file_prefix, verify_required_fields

logger = logging.getLogger(__name__)


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
    missing_fields = verify_required_fields({
        "file_name": file_name,
        "site": site,
    })
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for get_file_text: {list_str}")
        return ""

    file_name = ensure_file_prefix(file_name)

    if site is None:
        logger.error("Site is None after validation check")
        return ""

    try:
        page = site.pages[file_name]
        return page.text()
    except Exception as exc:
        logger.exception(f"Failed to retrieve wikitext for {file_name}", exc_info=exc)
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
    missing_fields = verify_required_fields({
        "original_file": original_file,
        "updated_file_text": updated_file_text,
        "site": site,
    })
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_file_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    original_file = ensure_file_prefix(original_file)

    summary = "Adding/updating {{Image extracted}}"

    try:
        page = site.pages[original_file]
        page.edit(updated_file_text, summary=summary)
        return {"success": True}
    except Exception as exc:
        error_msg = str(exc)
        logger.exception(f"Failed to update wikitext for {original_file}", exc_info=exc)
        return {"success": False, "error": error_msg}


def get_page_text(
    page_name: str,
    site: mwclient.Site | None,
) -> str:
    """
    Get the wikitext of any page on Wikimedia Commons.

    Args:
        page_name: The name of the page (e.g., "Template:OWID/Barley yields").
        site: Authenticated mwclient.Site object for Commons.

    Returns:
        The wikitext of the page, or an empty string if it cannot be retrieved.
    """
    missing_fields = verify_required_fields({
        "page_name": page_name,
        "site": site,
    })
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for get_page_text: {list_str}")
        return ""

    try:
        page = site.pages[page_name]
        return page.text()
    except Exception as exc:
        logger.exception(f"Failed to retrieve wikitext for {page_name}", exc_info=exc)
        return ""


def update_page_text(
    page_name: str,
    updated_text: str,
    site: mwclient.Site | None,
    summary: str = "",
) -> dict:
    """
    Update the wikitext of any page on Wikimedia Commons.

    Args:
        page_name: The name of the page to update.
        updated_text: The new wikitext for the page.
        site: Authenticated mwclient.Site object for Commons.
        summary: Edit summary.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str).
    """
    missing_fields = verify_required_fields({
        "page_name": page_name,
        "updated_text": updated_text,
        "site": site,
    })
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_page_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    try:
        page = site.pages[page_name]
        page.edit(updated_text, summary=summary)
        return {"success": True}
    except Exception as exc:
        error_msg = str(exc)
        logger.exception(f"Failed to update wikitext for {page_name}", exc_info=exc)
        return {"success": False, "error": error_msg}


__all__ = [
    "get_file_text",
    "update_file_text",
    "get_page_text",
    "update_page_text",
]
