from __future__ import annotations

import logging
from typing import Any

from ..database.services import ChartAndTemplate

logger = logging.getLogger(__name__)


def make_charts_summary(all_charts: list[ChartAndTemplate]) -> dict[str, Any]:

    total = len(all_charts)
    is_published = 0
    has_template = 0
    with_map_tab = 0
    with_timeline = 0
    with_source = 0

    # Single-pass loop to build data and collect summary statistics
    for c in all_charts:
        chart = c.chart
        # Update summary metrics
        if chart.is_published:
            is_published += 1

        if chart.source:
            with_source += 1

        if c.template_title:
            has_template += 1

        if chart.has_map_tab:
            with_map_tab += 1

        if chart.has_timeline:
            with_timeline += 1

    summary = {
        "total": total,
        "published": {"with": is_published, "without": total - is_published},
        "template": {"with": has_template, "without": total - has_template},
        "map_tab": {"with": with_map_tab, "without": total - with_map_tab},
        "timeline": {"with": with_timeline, "without": total - with_timeline},
        "source": {"with": with_source, "without": total - with_source},
    }

    return summary


__all__ = [
    "make_charts_summary",
]
