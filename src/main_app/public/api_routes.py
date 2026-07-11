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

    def _setup_routes(self) -> None:
        @self.bp.get("/templates")
        def templates_list():
            templates: list[TemplateRecord] = list_templates()

            data = []
            with_main_file = 0
            with_last_world_file = 0
            with_last_world_year = 0
            with_source = 0

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

            summary = {
                "total": len(templates),
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

            summary = {
                "total": len(all_charts),
                "published": {"with": 0, "without": 0},
                "template": {"with": 0, "without": 0},
                "map_tab": {"with": 0, "without": 0},
                "timeline": {"with": 0, "without": 0},
            }

            data: list[dict[str, Any]] = []
            for c in all_charts:
                # 1. Update summary
                if c.is_published:
                    summary["published"]["with"] += 1
                else:
                    summary["published"]["without"] += 1

                temp = charts_temps.get(c.chart_id)
                has_template = temp and temp.template_title
                if has_template:
                    summary["template"]["with"] += 1
                else:
                    summary["template"]["without"] += 1

                if c.has_map_tab:
                    summary["map_tab"]["with"] += 1
                else:
                    summary["map_tab"]["without"] += 1

                if c.has_timeline:
                    summary["timeline"]["with"] += 1
                else:
                    summary["timeline"]["without"] += 1

                # 2. Filtering and data enrichment
                should_include = True
                if template_filter == "has_template" and not has_template:
                    should_include = False
                elif template_filter == "no_template" and has_template:
                    should_include = False

                if should_include:
                    c_json = c.to_dict()
                    c_json["template_id"] = temp.template_id if temp else None
                    c_json["template_title"] = temp.template_title if temp else None
                    data.append(c_json)

            return jsonify({"data": data, "summary": summary, "selected_template": template_filter})


__all__ = [
    "ApiRoutes",
]
