from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify

from ..db.models import OwidChartRecord, OwidChartTemplateView, TemplateRecord
from ..db.services import (
    list_charts_with_templates,
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

    def make_charts_summary(
        self,
        results: list[tuple[OwidChartRecord, int | None, str | None]],
        template_filter: str,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        data: list[dict[str, Any]] = []
        total = len(results)
        published_with = 0
        template_with = 0
        map_tab_with = 0
        timeline_with = 0

        # Single-pass loop to build data and collect summary statistics
        for c, t_id, t_title in results:
            # Update summary metrics
            if c.is_published:
                published_with += 1

            has_template = bool(t_title)

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
                c_json["template_id"] = t_id
                c_json["template_title"] = t_title
                data.append(c_json)

        summary = {
            "total": total,
            "published": {"with": published_with, "without": total - published_with},
            "template": {"with": template_with, "without": total - template_with},
            "map_tab": {"with": map_tab_with, "without": total - map_tab_with},
            "timeline": {"with": timeline_with, "without": total - timeline_with},
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

                if t.last_world_file is not None:
                    with_last_world_file += 1

                if t.last_world_year is not None:
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
            all_charts_templates: list[OwidChartTemplateView] = list_owid_charts_templates()

            data = [c.to_dict() for c in all_charts_templates if c.template_id]
            return jsonify(data)

        @self.bp.get("/owidcharts/")
        @self.bp.get("/owidcharts/<string:template_filter>")
        def owid_charts_list(template_filter: str = ""):
            results = list_charts_with_templates()

            summary, data = self.make_charts_summary(results, template_filter)

            return jsonify({"data": data, "summary": summary, "selected_template": template_filter})


__all__ = [
    "ApiRoutes",
]
