"""OWID Charts public routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

from ...db.services import list_charts, list_published_charts

bp_owid_charts = Blueprint("owid_charts", __name__, url_prefix="/owidcharts")
logger = logging.getLogger(__name__)


@bp_owid_charts.route("/", methods=["GET"])
def index() -> str:
    """Display a list of all published OWID charts."""
    charts = list_published_charts()
    all_charts = list_charts()

    logger.info(f"Public charts page: {len(charts)} published, {len(all_charts)} total")

    for chart in charts:
        logger.debug(f"  Published chart: {chart.slug} - {chart.title}")

    return render_template("owid_charts/index.html", charts=charts)


@bp_owid_charts.get("/all")
def all_charts() -> str:
    """Display ALL charts (including unpublished) for debugging."""
    charts = list_charts()
    logger.info(f"All charts page: {len(charts)} total charts")
    return render_template("owid_charts/all_charts.html", charts=charts)


__all__ = [
    "bp_owid_charts",
]
