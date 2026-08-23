from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify

from ..api_services.files_service.file_langs import get_file_languages
from ..database.models import TemplateRecord
from ..database.services import (
    ChartAndTemplate,
    ChartsAndTemplatesService,
    OwidChartsService,
    TemplateService,
    ViewsService,
)
from ..services.owid_charts_utils import make_charts_summary

logger = logging.getLogger(__name__)


class ApiRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self.owid_charts_service = OwidChartsService()
        self.views_service = ViewsService()
        self.templates_service = TemplateService()
        self.charts_and_tmps_service = ChartsAndTemplatesService()
        self._setup_routes()

    def _setup_routes(self) -> None:

        routes = [
            ("/templates", "GET", self.templates_list),
            ("/templates/<string:filter>", "GET", self.templates_list),
            ("/templates-mismatched-years", "GET", self.templates_mismatched_years_list),
            ("/templates-need-update", "GET", self.templates_need_update_list),
            ("/owidcharts/", "GET", self.owid_charts_list),
            ("/owidcharts/<string:template_filter>", "GET", self.owid_charts_list),
            ("/languages/<path:file_name>", "GET", self.file_languages),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(target)

    def templates_list(self, filter: str = ""):
        templates: list[TemplateRecord] = self.templates_service.list()

        data: list[dict[str, Any]] = []
        with_main_file = 0
        with_last_world_file = 0
        with_last_world_year = 0
        with_source = 0

        if filter == "has_file":
            templates = [x for x in templates if x.main_file]

        # Single-pass loop to build data and summary
        for t in templates:
            data.append(t.to_json())

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

        return jsonify({"summary": summary, "data": data})

    def templates_mismatched_years_list(self):
        try:
            templates = self.templates_service.list_templates_mismatched_years()
            data = [t.to_json() for t in templates]
        except Exception as e:
            logger.exception(e)
            return jsonify({"error": str(e)}), 500

        return jsonify({"data": data})

    def templates_need_update_list(self):
        templates = self.views_service.list_templates_need_update()

        data = [t.to_json() for t in templates]

        return jsonify({"data": data})

    def file_languages(self, file_name: str):
        result = get_file_languages(file_name)
        error = result.error
        langs = result.langs or []
        if error or not langs:
            return jsonify({"error": error or "No languages found"}), 404
        return jsonify(langs)

    def owid_charts_list(self, template_filter: str = ""):
        # Optimize: use single-query list_all() with fallback
        charts_with_templates: list[ChartAndTemplate] = self.charts_and_tmps_service.list_all()

        charts_data: list[dict[str, Any]] = [x.to_dict_joined(template_filter) for x in charts_with_templates]
        summary = make_charts_summary(charts_with_templates)
        data = [x for x in charts_data if x]

        results = {
            "summary": summary,
            "selected_template": template_filter,
            "data": data,
        }
        return jsonify(results)


__all__ = [
    "ApiRoutes",
]
