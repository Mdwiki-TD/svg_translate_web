"""OWID Charts public routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

from ...db.services import OwidChartsService

logger = logging.getLogger(__name__)


class OwidChartsRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self.owid_charts_service = OwidChartsService()
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        def index() -> str:
            """Display a list of all published OWID charts."""
            charts = self.owid_charts_service.list_published_charts()
            total_charts = self.owid_charts_service.count_charts()

            logger.info(f"Public charts page: {len(charts)} published, {total_charts} total")

            return render_template("owid_charts/index.html", charts=charts)

        @self.bp.get("/all")
        def all_charts() -> str:
            """Display ALL charts (including unpublished) for debugging."""
            charts = self.owid_charts_service.list_charts()
            logger.info(f"All charts page: {len(charts)} total charts")
            return render_template("owid_charts/all_charts.html", charts=charts)


__all__ = [
    "OwidChartsRoutes",
]
