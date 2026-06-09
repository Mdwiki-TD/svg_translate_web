""" """

from __future__ import annotations

import logging
from typing import Any

import mwclient

from ..utils.verify import verify_required_fields
from .mwclient_page import MwClientPage

logger = logging.getLogger(__name__)


def is_page_exists(page_title: str, site: mwclient.Site) -> bool:
    return MwClientPage(page_title, site).check_exists()


def is_redirect(page_title: str, site: mwclient.Site) -> bool:
    return MwClientPage(page_title, site).is_redirect()


def _edit_page(site: mwclient.Site, title: str, text: str, summary: str, nocreate: bool = True) -> dict[str, Any]:
    return MwClientPage(title, site).edit_page(text, summary, nocreate=nocreate)


def edit_page(site: mwclient.Site, title: str, text: str, summary: str) -> dict[str, Any]:
    """ """
    missing_fields = verify_required_fields({"title": title, "text": text, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for edit_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}
    return _edit_page(site, title, text, summary, nocreate=True)


def move_page(
    site: mwclient.Site | None,
    title: str,
    new_title: str,
    reason: str = "",
    move_talk: bool = True,
    no_redirect: bool = False,
) -> dict[str, Any]:
    """
    Move (rename) a page on Wikimedia Commons.

    Args:
        site: Authenticated mwclient.Site object for Commons.
        title: Current page title (e.g. "Template:OWID/foo").
        new_title: Target page title (e.g. "Template:OWID/Foo").
        reason: Move reason / log summary on the wiki.
        move_talk: Also move the associated talk page.
        no_redirect: Do not leave a redirect at the old title (requires
            the ``suppressredirect`` user right).

    Returns:
        A dictionary with ``success`` (bool) and ``error``/``details`` on failure,
        matching the shape returned by :func:`create_page` / :func:`edit_page`.
    """
    missing_fields = verify_required_fields({"title": title, "new_title": new_title, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for move_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return MwClientPage(title, site).move_page(
        new_title,
        reason=reason,
        move_talk=move_talk,
        no_redirect=no_redirect,
    )


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

    Args:
        page_name: The name of the page to update.
        updated_text: The new wikitext content.
        site: Authenticated mwclient.Site object for Commons.
        summary: Edit summary.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str) on failure.
    """
    missing_fields = verify_required_fields({"page_name": page_name, "updated_text": updated_text, "site": site})
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_page_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return _edit_page(site, page_name, updated_text, summary, nocreate=True)


def get_page_text(
    page_title: str,
    site: mwclient.Site | None,
) -> str:
    """
    Get the wikitext of any page.

    Args:
        page_title: The name of the page (e.g., "Barley yields").
        site: Authenticated mwclient.Site object.

    Returns:
        The wikitext of the page, or an empty string if it cannot be retrieved.
    """
    missing_fields = verify_required_fields(
        {
            "page_title": page_title,
            "site": site,
        }
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for get_page_text: {list_str}")
        return ""

    try:
        page = site.pages[page_title]
        return page.text()
    except Exception as exc:
        logger.exception(f"Failed to retrieve wikitext for {page_title}", exc_info=exc)
        return ""


__all__ = [
    "is_page_exists",
    "is_redirect",
    "create_page",
    "get_page_text",
    "move_page",
    "update_page_text",
]
