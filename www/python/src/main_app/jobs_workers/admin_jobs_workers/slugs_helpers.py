""" """

from __future__ import annotations

import logging
from typing import Any

from ...database.services import OwidSlugRedirectsService
from ...database.templates_utils import extract_slug

logger = logging.getLogger(__name__)


def check_slugs_url(slug_to_check: str, original_chart_url: str | None) -> bool:
    """
    Check if the slug has a redirect and add it to the database if needed.
    """
    if not original_chart_url:
        return False

    original_slug = extract_slug(original_chart_url)

    if not original_slug:
        return False

    if original_slug == slug_to_check:
        return False

    try:
        OwidSlugRedirectsService().add_new_slug_redirect(slug=slug_to_check, redirect_to=original_slug)
        return True
    except Exception as e:
        logger.error("Error adding slug redirect: %s", e)

    return False


def check_slugs(slug_to_check: str, metadata: dict[str, Any]) -> bool:
    """
    Check if the slug has a redirect and add it to the database if needed.
    """
    original_chart_url = metadata.get("chart", {}).get("originalChartUrl", "")

    return check_slugs_url(
        slug_to_check=slug_to_check,
        original_chart_url=original_chart_url,
    )


__all__ = [
    "check_slugs",
]
