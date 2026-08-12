from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify

from ..api_services.files_service.file_langs import get_file_languages
from ..db.models import TemplateRecord
from ..db.services import (
    ChartAndTemplate,
    ChartsAndTemplatesService,
    OwidChartsService,
    TemplateService,
    ViewsService,
)
from ..shared.owid_charts_utils import make_charts_summary

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
        self.bp.get("/templates")(self.templates_list)
        self.bp.get("/templates-mismatched-years")(self.templates_mismatched_years_list)
        self.bp.get("/templates-need-update")(self.templates_need_update_list)

        self.bp.get("/owidcharts/")(self.owid_charts_list)
        self.bp.get("/owidcharts/<string:template_filter>")(self.owid_charts_list)

        self.bp.get("/languages/<path:file_name>")(self.file_languages)

    def templates_list(self):
        templates: list[TemplateRecord] = self.templates_service.list()

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

        return jsonify({"summary": summary, "data": data})

    def templates_mismatched_years_list(self):
        try:
            templates = self.templates_service.list_templates_mismatched_years()
            data = [t.to_dict() for t in templates]
        except Exception as e:
            logger.exception(e)
            return jsonify({"error": str(e)}), 500

        return jsonify({"data": data})

    def templates_need_update_list(self):
        templates = self.views_service.list_templates_need_update()

        data = [t.to_dict() for t in templates]

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
