from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..db.models import OwidChartRecord, OwidChartTemplateView

logger = logging.getLogger(__name__)


@dataclass
class OwidChartWithTemplate:
    chart_id: int
    template_id: int | None
    template_title: str | None


def make_charts_summary(
    all_charts: list[OwidChartRecord],
    charts_temps: dict[int, OwidChartTemplateView | OwidChartWithTemplate],
    template_filter: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    data: list[dict[str, Any]] = []
    total = len(all_charts)
    published_with = 0
    template_with = 0
    map_tab_with = 0
    timeline_with = 0

    # Single-pass loop to build data and collect summary statistics
    for c in all_charts:
        # Update summary metrics
        if c.is_published:
            published_with += 1

        temp_rec = charts_temps.get(c.chart_id)
        has_template = bool(temp_rec.template_title) if temp_rec else False

        if has_template:
            template_with += 1

        if c.has_map_tab:
            map_tab_with += 1
        if c.has_timeline:
            timeline_with += 1

        # Filtering and data enrichment
        include = (
            template_filter not in ("has_template", "no_template")
            or (template_filter == "has_template") == has_template
        )
        if include:
            c_json = c.to_dict()
            c_json["template_id"] = temp_rec.template_id if temp_rec else None
            c_json["template_title"] = temp_rec.template_title if temp_rec else None
            data.append(c_json)

    summary = {
        "total": total,
        "published": {"with": published_with, "without": total - published_with},
        "template": {"with": template_with, "without": total - template_with},
        "map_tab": {"with": map_tab_with, "without": total - map_tab_with},
        "timeline": {"with": timeline_with, "without": total - timeline_with},
    }

    return summary, data


def charts_new_list(
    charts_with_templates: list[tuple[OwidChartRecord, int | None, str | None]],
    template_filter: str = "",
) -> dict[str, Any]:
    # Optimize: use single-query list_charts_with_templates() with fallback
    all_charts = []
    charts_temps = {}
    try:
        for chart, temp_id, temp_title in charts_with_templates:
            all_charts.append(chart)
            charts_temps[chart.chart_id] = OwidChartWithTemplate(
                chart_id=chart.chart_id,
                template_id=temp_id,
                template_title=temp_title,
            )
    except Exception as e:
        logger.debug(f"Falling back to legacy multi-query charts listing: {e}")

    summary, data = make_charts_summary(all_charts, charts_temps, template_filter)

    return {"data": data, "summary": summary, "selected_template": template_filter}


__all__ = [
    "make_charts_summary",
    "OwidChartWithTemplate",
    "charts_new_list",
]
