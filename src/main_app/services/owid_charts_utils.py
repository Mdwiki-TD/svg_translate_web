from __future__ import annotations

import logging
from typing import Any

from ..database.services import ChartAndTemplate

logger = logging.getLogger(__name__)


def make_charts_summary(all_charts: list[ChartAndTemplate]) -> dict[str, Any]:

    total = len(all_charts)
    published_with = 0
    template_with = 0
    map_tab_with = 0
    timeline_with = 0

    # Single-pass loop to build data and collect summary statistics
    for c in all_charts:
        chart = c.chart
        # Update summary metrics
        if chart.is_published:
            published_with += 1

        if c.template_title:
            template_with += 1

        if chart.has_map_tab:
            map_tab_with += 1

        if chart.has_timeline:
            timeline_with += 1

    summary = {
        "total": total,
        "published": {"with": published_with, "without": total - published_with},
        "template": {"with": template_with, "without": total - template_with},
        "map_tab": {"with": map_tab_with, "without": total - map_tab_with},
        "timeline": {"with": timeline_with, "without": total - timeline_with},
    }

    return summary


__all__ = [
    "make_charts_summary",
]
