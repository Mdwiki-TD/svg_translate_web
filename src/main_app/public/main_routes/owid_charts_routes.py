"""OWID Charts public routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

from ...db.services import ChartsAndTemplatesService  # , OwidChartsService
from ...db.services.charts_and_templates_service import ChartAndTemplate

logger = logging.getLogger(__name__)


class OwidChartsRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        # self.owid_charts_service = OwidChartsService()
        self.charts_and_tmps_service = ChartsAndTemplatesService()
        self._setup_routes()

    def _setup_routes(self) -> None:
        routes = [
            ("/", "GET", self.index),
            ("/all", "GET", self.all_charts),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(target)

    def index(self) -> str:
        """Display a list of all published OWID charts."""
        # charts = self.owid_charts_service.list_published_charts()
        charts_with_templates: list[ChartAndTemplate] = self.charts_and_tmps_service.list_all()
        charts = [x.to_dict_joined() for x in charts_with_templates if x.chart.is_published]

        logger.info(f"Public charts page: {len(charts)} published")

        return render_template(
            "owid_charts/index.html",
            charts=charts,
        )

    def all_charts(self) -> str:
        """Display ALL charts (including unpublished) for debugging."""
        # charts = self.owid_charts_service.list_charts()
        charts_with_templates: list[ChartAndTemplate] = self.charts_and_tmps_service.list_all()
        charts = [x.to_dict_joined() for x in charts_with_templates]
        logger.info(f"All charts page: {len(charts)} total charts")
        return render_template(
            "owid_charts/all_charts.html",
            charts=charts,
        )


__all__ = [
    "OwidChartsRoutes",
]
