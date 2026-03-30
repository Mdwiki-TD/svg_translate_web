""" """

from __future__ import annotations

import logging

import mwclient

from ..utils.verify import verify_required_fields
from ..utils.wikitext import ensure_file_prefix
from .mwclient_page import MwClientPage

logger = logging.getLogger(__name__)


def is_page_exists(page_title: str, site: mwclient.Site) -> bool:
    return MwClientPage(page_title, site).check_exists()


def edit_page(site, title, text, summary) -> dict[str, any]:
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
    missing_fields = verify_required_fields(
        {"page_name": page_name, "wikitext": wikitext, "site": site}
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for create_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return edit_page(site, page_name, wikitext, summary)


def update_file_text(
    original_file: str,
    updated_file_text: str,
    site: mwclient.Site | None,
) -> dict:
    """
    Update the wikitext of the original file.

    Args:
        original_file: The name of the original file on Commons.
        updated_file_text: The new wikitext content.
        site: Authenticated mwclient.Site object for Commons.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str) on failure.
    """
    missing_fields = verify_required_fields(
        {
            "original_file": original_file,
            "updated_file_text": updated_file_text,
            "site": site,
        }
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_file_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    original_file = ensure_file_prefix(original_file)

    summary = "Adding/updating {{Image extracted}}"

    return edit_page(site, original_file, updated_file_text, summary)


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
        updated_text: The new wikitext content.
        site: Authenticated mwclient.Site object for Commons.
        summary: Edit summary.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str) on failure.
    """
    missing_fields = verify_required_fields(
        {"page_name": page_name, "updated_text": updated_text, "site": site}
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_page_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return edit_page(site, page_name, updated_text, summary)


def is_pages_exists(
    titles: list[str],
    site: mwclient.Site,
) -> dict[str, bool]:
    result = {}

    for i in range(0, len(titles), 50):
        group = titles[i : i + 50]

        group = [f"File:{file.removeprefix('File:')}" for file in group]

        json1 = site.get("query", titles="|".join(group))

        query = json1.get("query", {})

        normalized = {red["to"]: red["from"] for red in query.get("normalized", [])}

        query_pages = query.get("pages", {})
        for _, kk in query_pages.items():
            title = kk.get("title", "")
            if title:
                original_title = normalized.get(title, title)
                result[original_title] = "missing" not in kk

    return result


__all__ = [
    "create_page",
    "is_page_exists",
    "update_file_text",
    "update_page_text",
]
