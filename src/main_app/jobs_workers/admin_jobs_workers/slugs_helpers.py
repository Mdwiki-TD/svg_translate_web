""" """

from __future__ import annotations

import logging
from typing import Any

from ...db.templates_utils import extract_slug
from ...db.services import add_new_slug_redirect

logger = logging.getLogger(__name__)


def check_slugs(slug_to_check: str, metadata: dict[str, Any]) -> bool:
    """
    Check if the slug has a redirect and add it to the database if needed.
    """
    original_chart_url = metadata.get("chart", {}).get("originalChartUrl", "")
    if not original_chart_url:
        return False

    original_slug = extract_slug(original_chart_url)

    if not original_slug:
        return False

    if original_slug == slug_to_check:
        return False

    try:
        add_new_slug_redirect(slug=slug_to_check, redirect_to=original_slug)
        return True
    except Exception as e:
        logger.error(f"Error adding slug redirect: {e}")

    return False
__all__ = [
    "check_slugs",
]
