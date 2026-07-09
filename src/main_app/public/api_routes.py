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

            data: list[dict[str, Any]] = []
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

            data: list[dict[str, Any]] = []
            total = len(all_charts)
            published_with = 0
            published_without = 0
            template_with = 0
            template_without = 0
            map_tab_with = 0
            map_tab_without = 0
            timeline_with = 0
            timeline_without = 0

            for c in all_charts:
                temp = charts_temps.get(c.chart_id)
                temp_title = temp.template_title if temp else None

                # Update summary metrics
                if c.is_published:
                    published_with += 1
                else:
                    published_without += 1

                if temp_title:
                    template_with += 1
                else:
                    template_without += 1

                if c.has_map_tab:
                    map_tab_with += 1
                else:
                    map_tab_without += 1

                if c.has_timeline:
                    timeline_with += 1
                else:
                    timeline_without += 1

                # Apply filter and build data
                include = True
                if template_filter == "has_template" and not temp_title:
                    include = False
                elif template_filter == "no_template" and temp_title:
                    include = False

                if include:
                    c_json = c.to_dict()
                    c_json["template_id"] = temp.template_id if temp else None
                    c_json["template_title"] = temp_title
                    data.append(c_json)

            summary = {
                "total": total,
                "published": {"with": published_with, "without": published_without},
                "template": {"with": template_with, "without": template_without},
                "map_tab": {"with": map_tab_with, "without": map_tab_without},
                "timeline": {"with": timeline_with, "without": timeline_without},
            }

            return jsonify({"data": data, "summary": summary, "selected_template": template_filter})


__all__ = [
    "ApiRoutes",
]
