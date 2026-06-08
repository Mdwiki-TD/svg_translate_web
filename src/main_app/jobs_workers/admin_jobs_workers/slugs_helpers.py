""" """

from __future__ import annotations

import logging

from ...db.services import add_new_slug_redirect

logger = logging.getLogger(__name__)


def check_slugs(_slug_to_check, metadata) -> bool:
    original_chart_url = metadata.get("chart", {}).get("originalChartUrl", "")
    if not original_chart_url or "/grapher/" not in original_chart_url:
        return False

    original_slug = original_chart_url.split("/grapher/", maxsplit=1)[1].split("?")[0]
    if original_slug == _slug_to_check:
        return False

    try:
        add_new_slug_redirect(slug=_slug_to_check, redirect_to=original_slug)
        return True
    except Exception as e:
        logger.error(f"Error adding slug redirect: {e}")

    return False
