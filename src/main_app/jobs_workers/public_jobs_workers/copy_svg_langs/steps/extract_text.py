"""Step for extracting wikitext for a Commons file."""

from __future__ import annotations

import logging
from typing import Any

import mwclient

from .....api_services.mwclient_page import MwClientPage

logger = logging.getLogger(__name__)


def extract_text_step(title: str, site: mwclient.Site | None = None) -> dict[str, Any]:
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

    text = MwClientPage(title, site).get_text()

    if not text:
        logger.error(f"No wikitext found for title: {title}")
        return {"success": False, "text": "", "error": "No wikitext found"}

    return {"success": True, "text": text, "error": None}


__all__ = [
    "extract_text_step",
]
