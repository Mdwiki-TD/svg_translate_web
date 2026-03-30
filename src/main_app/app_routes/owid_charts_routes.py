"""OWID Charts public routes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
)

from ..owid_charts_service import list_published_charts

bp_owid_charts = Blueprint("owid_charts", __name__, url_prefix="/owid-charts")
logger = logging.getLogger(__name__)


@bp_owid_charts.get("/")
def index():
    """Display a list of all published OWID charts."""
    charts = list_published_charts()
    return render_template("owid_charts/index.html", charts=charts)


__all__ = ["bp_owid_charts"]
