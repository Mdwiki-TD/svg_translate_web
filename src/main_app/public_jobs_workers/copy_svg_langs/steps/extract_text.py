"""Step for extracting wikitext for a Commons file."""

from __future__ import annotations

import logging
from typing import Any

from ....api_services.text_bot import get_wikitext

logger = logging.getLogger(__name__)


def extract_text_step(title: str) -> dict[str, Any]:
    """Fetch wikitext for a Commons file.

    Args:
        title: Commons title whose wikitext should be retrieved.

    Returns:
        dict with keys: success (bool), text (str), error (str|None)
    """
    logger.info(f"Extracting wikitext for: {title}")
    text = get_wikitext(title)

    if not text:
        logger.error(f"No wikitext found for title: {title}")
        return {"success": False, "text": "", "error": "No wikitext found"}

    return {"success": True, "text": text, "error": None}
