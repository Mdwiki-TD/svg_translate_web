""" """

from __future__ import annotations

import logging

import mwclient

from ..utils.verify import verify_required_fields

logger = logging.getLogger(__name__)


def is_page_exists(
    page_title: str,
    site: mwclient.Site | None,
) -> bool:

    page = site.Pages[page_title]

    if page.exists:
        logger.warning(f"File {page_title} already exists on Commons")
        return True
    return False


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
        A dictionary with 'success' (bool) and optionally 'error' (str).
    """
    missing_fields = verify_required_fields(
        {
            "page_name": page_name,
            "wikitext": wikitext,
            "site": site,
        }
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for create_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    try:
        page = site.pages[page_name]
        page.edit(wikitext, summary=summary)
        return {"success": True}
    except Exception as exc:
        error_msg = str(exc)
        logger.exception(f"Failed to create page {page_name}", exc_info=exc)
        return {"success": False, "error": error_msg}


__all__ = [
    "create_page",
    "is_page_exists",
]
