"""OWID Charts public routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

from ...db.services import list_charts, list_published_charts

logger = logging.getLogger(__name__)


class OwidChartsRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        def index() -> str:
            """Display a list of all published OWID charts."""
            charts = list_published_charts()
            all_charts = list_charts()

            logger.info(f"Public charts page: {len(charts)} published, {len(all_charts)} total")

            for chart in charts:
                logger.debug(f"  Published chart: {chart.slug} - {chart.title}")

            return render_template("owid_charts/index.html", charts=charts)

        @self.bp.get("/all")
        def all_charts() -> str:
            """Display ALL charts (including unpublished) for debugging."""
            charts = list_charts()
            logger.info(f"All charts page: {len(charts)} total charts")
            return render_template("owid_charts/all_charts.html", charts=charts)


__all__ = [
    "OwidChartsRoutes",
]
