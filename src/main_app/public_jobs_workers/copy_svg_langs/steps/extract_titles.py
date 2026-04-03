"""Step for extracting SVG titles from wikitext."""

from __future__ import annotations

import logging
from typing import Any

from ....utils.wikitext import get_files_list_data

logger = logging.getLogger(__name__)


def extract_titles_step(
    text: str,
    manual_main_title: str | None = None,
    titles_limit: int | None = None,
) -> dict[str, Any]:
    """Extract SVG titles from wikitext.

    Args:
        text: Wikitext retrieved from the main Commons page.
        manual_main_title: Optional title to use instead of the extracted main_title.
        titles_limit: Optional maximum number of titles to keep.

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
        return {"success": False, "main_title": main_title, "titles": titles or [], "error": error, "message": "", }

    message = f"Found {len(titles)} titles"
    if titles_limit and titles_limit > 0 and len(titles) > titles_limit:
        logger.info(f"Limiting titles from {len(titles)} to {titles_limit}")
        titles = titles[:titles_limit]

    return {"success": True, "main_title": main_title, "titles": titles, "error": None, "message": message, }
