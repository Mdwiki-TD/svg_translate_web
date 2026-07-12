from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify

from ..db.models import OwidChartRecord, OwidChartTemplateRecord, TemplateRecord
from ..db.services import (
    list_charts,
    list_owid_charts_templates,
    list_templates,
    list_templates_mismatched_years,
    list_templates_need_update,
)

logger = logging.getLogger(__name__)


class ApiRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def get_tmp_title(self, charts_temps, chart_id):
        chart_data = charts_temps.get(chart_id)
        if chart_data:
            return chart_data.template_title
        return None

    def make_charts_summary(self, all_charts, charts_temps, template_filter) -> dict[str, Any]:
        data: list[dict[str, Any]] = []
        total = len(all_charts)
        pub_with = 0
        temp_with = 0
        map_with = 0
        time_with = 0

        # Single-pass loop to build data and collect summary statistics
        for c in all_charts:
            if c.is_published:
                pub_with += 1

            temp_rec = charts_temps.get(c.chart_id)
            has_temp = temp_rec is not None and temp_rec.template_title is not None
            if has_temp:
                temp_with += 1

            if c.has_map_tab:
                map_with += 1
            if c.has_timeline:
                time_with += 1

            # Filtering and data enrichment
            include = True
            if template_filter == "has_template":
                include = has_temp
            elif template_filter == "no_template":
                include = not has_temp

            if include:
                c_json = c.to_dict()
                c_json["template_id"] = temp_rec.template_id if temp_rec else None
                c_json["template_title"] = temp_rec.template_title if temp_rec else None
                data.append(c_json)

        summary = {
            "total": total,
            "published": {"with": pub_with, "without": total - pub_with},
            "template": {"with": temp_with, "without": total - temp_with},
            "map_tab": {"with": map_with, "without": total - map_with},
            "timeline": {"with": time_with, "without": total - time_with},
        }

        return summary, data

    def _setup_routes(self) -> None:
        @self.bp.get("/templates")
        def templates_list():
            templates: list[TemplateRecord] = list_templates()

            data: list[dict[str, Any]] = []
            with_main_file = 0
            with_last_world_file = 0
            with_last_world_year = 0
            with_source = 0

            # Single-pass loop to build data and summary
            for t in templates:
                data.append(t.to_dict())
                if t.main_file:
                    with_main_file += 1
                if t.last_world_file:
                    with_last_world_file += 1
                if t.last_world_year:
                    with_last_world_year += 1
                if t.source:
                    with_source += 1

            total = len(templates)
            summary = {
                "total": total,
                "with_main_file": with_main_file,
                "with_last_world_file": with_last_world_file,
                "with_last_world_year": with_last_world_year,
                "with_source": with_source,
            }

            return jsonify({"data": data, "summary": summary})

        @self.bp.get("/templates-mismatched-years")
        def templates_mismatched_years_list():
            try:
                templates = list_templates_mismatched_years()
                data = [t.to_dict() for t in templates]
            except Exception as e:
                logger.exception(e)
                return jsonify({"error": str(e)}), 500

            return jsonify({"data": data})

        @self.bp.get("/templates-need-update")
        def templates_need_update_list():
            templates = list_templates_need_update()

            data = [t.to_dict() for t in templates]

            return jsonify({"data": data})

        @self.bp.get("/charts_templates")
        def charts_templates():
            all_charts_templates: list[OwidChartTemplateRecord] = list_owid_charts_templates()

            data = [c.to_dict() for c in all_charts_templates if c.template_id]
            return jsonify(data)

        @self.bp.get("/owidcharts/")
        @self.bp.get("/owidcharts/<string:template_filter>")
        def owid_charts_list(template_filter: str = ""):
            all_charts: list[OwidChartRecord] = list_charts()
            all_charts_templates: list[OwidChartTemplateRecord] = list_owid_charts_templates()

            charts_temps = {c.chart_id: c for c in all_charts_templates}

            summary, data = self.make_charts_summary(all_charts, charts_temps, template_filter)

            return jsonify({"data": data, "summary": summary, "selected_template": template_filter})


__all__ = [
    "ApiRoutes",
]
