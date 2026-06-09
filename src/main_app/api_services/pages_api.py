""" """

from __future__ import annotations

import logging
from typing import Any

import mwclient

from ..utils.verify import verify_required_fields
from .mwclient_page import MwClientPage

logger = logging.getLogger(__name__)

def edit_page(site: mwclient.Site, title: str, text: str, summary: str) -> dict[str, Any]:
    """ """
    missing_fields = verify_required_fields({"title": title, "text": text, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for edit_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}
    return MwClientPage(title, site).edit_page(text, summary)


def create_page(
    page_name: str,
    wikitext: str,
    site: mwclient.Site | None,
    summary: str = "",
) -> dict:
    """
    Create a new page on Wikimedia Commons.

    Args:
        page_name: The name of the page to create.
        wikitext: The wikitext content for the new page.
        site: Authenticated mwclient.Site object for Commons.
        summary: Edit summary.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str) on failure.
    """
    missing_fields = verify_required_fields({"page_name": page_name, "wikitext": wikitext, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for create_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return MwClientPage(page_name, site).create_page(wikitext, summary)


def update_page_text(
    page_name: str,
    updated_text: str,
    site: mwclient.Site | None,
    summary: str = "",
) -> dict:
    """
    Update the wikitext of any page on Wikimedia Commons.
    """
    missing_fields = verify_required_fields({"page_name": page_name, "updated_text": updated_text, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_page_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return MwClientPage(page_name, site).edit_page(updated_text, summary, nocreate=True)


__all__ = [
    "create_page",
    "update_page_text",
]
