"""Public JSON API routes exposed as MethodView classes."""

from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify
from flask.views import MethodView

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


class TemplatesListView(MethodView):
    """View to list templates with an aggregate summary as JSON."""

    def __init__(self) -> None:
        self.templates_service = TemplateService()

    def get(self, filter: str = "") -> str:
        """Return templates and summary counts as JSON."""
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


class TemplatesMismatchedYearsView(MethodView):
    """View to list templates whose years mismatch their charts."""

    def __init__(self) -> None:
        self.templates_service = TemplateService()

    def get(self) -> str:
        """Return mismatched-year templates as JSON."""
        try:
            templates = self.templates_service.list_templates_mismatched_years()
            data = [t.to_json() for t in templates]
        except Exception as e:
            logger.exception(e)
            return jsonify({"error": str(e)}), 500

        return jsonify({"data": data})


class TemplatesNeedUpdateListView(MethodView):
    """View to list templates that need a year update."""

    def __init__(self) -> None:
        self.views_service = ViewsService()

    def get(self) -> str:
        """Return templates needing an update as JSON."""
        templates = self.views_service.list_templates_need_update()

        data = [t.to_json() for t in templates]

        return jsonify({"data": data})


class FileLanguagesView(MethodView):
    """View to return the languages available for a single file."""

    def get(self, file_name: str) -> str:
        """Return the language list for ``file_name`` as JSON."""
        result = get_file_languages(file_name)
        error = result.error
        langs = result.langs or []
        if error or not langs:
            return jsonify({"error": error or "No languages found"}), 404
        return jsonify(langs)


class OwidChartsListView(MethodView):
    """View to list OWID charts, optionally filtered by template."""

    def __init__(self) -> None:
        self.owid_charts_service = OwidChartsService()
        self.charts_and_tmps_service = ChartsAndTemplatesService()

    def get(self, template_filter: str = "") -> str:
        """Return charts and summary counts as JSON."""
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


class ApiRoutes:
    """Registrar class to bind public API MethodViews to a Blueprint."""

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register public API URL rules on the provided blueprint."""
        templates_view = TemplatesListView.as_view("templates_list")
        bp.add_url_rule("/templates", view_func=templates_view)
        bp.add_url_rule("/templates/<string:filter>", view_func=templates_view)

        bp.add_url_rule(
            "/templates-mismatched-years",
            view_func=TemplatesMismatchedYearsView.as_view("templates_mismatched_years_list"),
        )
        bp.add_url_rule(
            "/templates-need-update",
            view_func=TemplatesNeedUpdateListView.as_view("templates_need_update_list"),
        )

        owid_view = OwidChartsListView.as_view("owid_charts_list")
        bp.add_url_rule("/owidcharts/", view_func=owid_view)
        bp.add_url_rule("/owidcharts/<string:template_filter>", view_func=owid_view)

        bp.add_url_rule("/languages/<path:file_name>", view_func=FileLanguagesView.as_view("file_languages"))


__all__ = [
    "ApiRoutes",
]
