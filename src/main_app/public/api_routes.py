from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify

from ..db.models import OwidChartRecord, OwidChartTemplateView, TemplateRecord
from ..db.services import (
    list_charts,
    list_charts_with_templates,
    list_owid_charts_templates,
    list_templates,
    list_templates_mismatched_years,
    list_templates_need_update,
)
from ..shared.owid_charts_utils import charts_new_list, make_charts_summary

logger = logging.getLogger(__name__)


class ApiRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.get("/templates")(self.templates_list)
        self.bp.get("/templates-mismatched-years")(self.templates_mismatched_years_list)
        self.bp.get("/templates-need-update")(self.templates_need_update_list)
        self.bp.get("/charts_templates")(self.charts_templates)

        self.bp.get("/owidcharts/")(self.owid_charts_list)
        self.bp.get("/owidcharts/<string:template_filter>")(self.owid_charts_list)

        self.bp.get("/owidcharts_new/")(self.owid_charts_list_new)
        self.bp.get("/owidcharts_new/<string:template_filter>")(self.owid_charts_list_new)

    def templates_list(self):
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

    def templates_mismatched_years_list(self):
        try:
            templates = list_templates_mismatched_years()
            data = [t.to_dict() for t in templates]
        except Exception as e:
            logger.exception(e)
            return jsonify({"error": str(e)}), 500

        return jsonify({"data": data})

    def templates_need_update_list(self):
        templates = list_templates_need_update()

        data = [t.to_dict() for t in templates]

        return jsonify({"data": data})

    def charts_templates(self):
        all_charts_templates: list[OwidChartTemplateView] = list_owid_charts_templates()

        data = [c.to_dict() for c in all_charts_templates if c.template_id]
        return jsonify(data)

    def owid_charts_list(self, template_filter: str = ""):
        all_charts: list[OwidChartRecord] = list_charts()
        all_charts_templates: list[OwidChartTemplateView] = list_owid_charts_templates()

        charts_temps = {c.chart_id: c for c in all_charts_templates}

        summary, data = make_charts_summary(all_charts, charts_temps, template_filter)

        return jsonify({"data": data, "summary": summary, "selected_template": template_filter})

    def owid_charts_list_new(self, template_filter: str = ""):
        charts_with_templates = list_charts_with_templates()
        results = charts_new_list(charts_with_templates, template_filter)
        return jsonify(results)


__all__ = [
    "ApiRoutes",
]
