from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..db.services import ChartAndTemplate

logger = logging.getLogger(__name__)


@dataclass
class OwidChartWithTemplate:
    chart_id: int
    template_id: int | None
    template_title: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "template_id": self.template_id,
            "template_title": self.template_title,
        }

def make_charts_summary( all_charts: list[ChartAndTemplate] ) -> dict[str, Any]:

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

        has_template = bool(c.template_title) if c.template_title else False

        if has_template:
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
    "OwidChartWithTemplate",
    "make_charts_summary",
]
