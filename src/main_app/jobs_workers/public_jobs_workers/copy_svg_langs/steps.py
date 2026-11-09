"""
Step for extracting wikitext for a Commons file.
Step for extracting SVG titles from wikitext.
"""

from __future__ import annotations

import logging
from typing import Any

from mwclient.client import Site

from ....api_services import MwClientPage
from ....utils.wikitext import get_files_list_data

logger = logging.getLogger(__name__)


def extract_text_step(title: str, site: Site | None = None) -> dict[str, Any]:
    """Fetch wikitext for a Commons file.

    Args:
        title: Commons title whose wikitext should be retrieved.

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    logger.info(f"Extracting wikitext for: {title}")
    if not title:
        logger.error("No title found")
        return {"success": False, "text": "", "error": "No title found"}

    try:
        text = MwClientPage(title, site).get_text()
    except Exception:
        logger.exception(f"Failed to fetch wikitext for title: {title}")
        return {"success": False, "text": "", "error": "Failed to fetch wikitext"}

    if not text:
        logger.error(f"No wikitext found for title: {title}")
        return {"success": False, "text": "", "error": "No wikitext found"}

    return {"success": True, "text": text, "error": None}


def extract_titles_step(
    text: str,
    manual_main_title: str | None = None,
) -> dict[str, Any]:
    """Extract SVG titles from wikitext.

    Args:
        text: Wikitext retrieved from the main Commons page.
        manual_main_title: Optional title to use instead of the extracted main_title.

    Returns:
        dict with keys: success (bool), main_title (str|None), titles (list[str]), error (str|None)
    """
    data = get_files_list_data(text)

    main_title = data["main_title"]
    titles = data["titles"]

    if manual_main_title:
        main_title = manual_main_title

    if not titles or not main_title:
        error = f"No titles or main title found. Manual main title was: '{manual_main_title}'"
        logger.error(error)
        return {
            "success": False,
            "main_title": main_title,
            "titles": titles or [],
            "error": error,
            "message": "",
        }

    message = f"Found {len(titles)} titles"

    return {
        "success": True,
        "main_title": main_title,
        "titles": titles,
        "error": None,
        "message": message,
    }


__all__ = [
    "extract_titles_step",
    "extract_text_step",
]
