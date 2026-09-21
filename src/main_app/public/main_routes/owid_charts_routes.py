"""OWID Charts public routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)
from flask.views import MethodView

from ...database.services import ChartsAndTemplatesService  # , OwidChartsService
from ...database.services.charts_and_templates_service import ChartAndTemplate

logger = logging.getLogger(__name__)


class OwidChartsIndexView(MethodView):
    """View to display a list of all published OWID charts."""

    def __init__(self) -> None:
        # self.owid_charts_service = OwidChartsService()
        self.charts_and_tmps_service = ChartsAndTemplatesService()

    def get(self) -> str:
        """Render the published charts page."""
        # charts = self.owid_charts_service.list_published_charts()
        charts_with_templates: list[ChartAndTemplate] = self.charts_and_tmps_service.list_all()
        charts = [x.to_dict_joined() for x in charts_with_templates if x.chart.is_published]

        logger.info(f"Public charts page: {len(charts)} published")

        return render_template(
            "owid_charts/index.html",
            charts=charts,
        )


class OwidChartsAllView(MethodView):
    """View to display ALL charts (including unpublished) for debugging."""

    def __init__(self) -> None:
        # self.owid_charts_service = OwidChartsService()
        self.charts_and_tmps_service = ChartsAndTemplatesService()

    def get(self) -> str:
        """Render the all charts page."""
        # charts = self.owid_charts_service.list_charts()
        charts_with_templates: list[ChartAndTemplate] = self.charts_and_tmps_service.list_all()
        charts = [x.to_dict_joined() for x in charts_with_templates]
        logger.info(f"All charts page: {len(charts)} total charts")
        return render_template(
            "owid_charts/all_charts.html",
            charts=charts,
        )


class OwidChartsRoutes:
    """Registrar class to bind public OWID charts MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register public OWID charts URL rules on the provided blueprint."""
        bp.add_url_rule("/", view_func=OwidChartsIndexView.as_view("index"))
        bp.add_url_rule("/all", view_func=OwidChartsAllView.as_view("all_charts"))


__all__ = [
    "OwidChartsRoutes",
]
