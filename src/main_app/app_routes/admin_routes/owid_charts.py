"""OWID Charts administration routes."""

from __future__ import annotations

import json
import logging
from typing import Any, List, Tuple

from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from sqlalchemy.exc import IntegrityError

from ...db.models import OwidChartRecord
from ...db.models.views import OwidChartTemplateRecord
from ...db.services import owid_charts_service
from ...db.services.views_service import list_owid_charts_templates
from ..admin.admins_required import admin_required

logger = logging.getLogger(__name__)


def create_json_file() -> Tuple[Any, int]:
    """Create a JSON file containing all charts data.

    Returns:
        Tuple of (response, status_code) where response is either a Flask
        response object for file download (status 200) or an error message
        string with appropriate status code (404 for no charts, 500 for errors).
    """
    try:
        charts: List[OwidChartRecord] = owid_charts_service.list_charts()

        all_charts_templates: list[OwidChartTemplateRecord] = list_owid_charts_templates()

        charts_temps = {c.chart_id: c.template_title for c in all_charts_templates}

        if not charts:
            return "No charts found to export.", 404

        charts_data: list[dict[str, Any]] = []
        for chart in charts:
            chart_data = {
                "chart_id": chart.chart_id,
                "slug": chart.slug,
                "title": chart.title,
                "has_map_tab": chart.has_map_tab,
                "max_time": chart.max_time,
                "min_time": chart.min_time,
                "default_tab": chart.default_tab,
                "is_published": chart.is_published,
                "single_year_data": chart.single_year_data,
                "len_years": chart.len_years,
                "has_timeline": chart.has_timeline,
                "template_id": None,
                "template_title": None,
            }
            if charts_temps.get(chart.chart_id):
                chart_data["template_id"] = chart.chart_id
                chart_data["template_title"] = charts_temps.get(chart.chart_id)

            charts_data.append(chart_data)

        json_content = json.dumps(charts_data, indent=2, ensure_ascii=False)

        response = make_response(json_content)
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Disposition"] = "attachment; filename=owid_charts.json"

        return response, 200

    except LookupError:
        logger.exception("Charts not found.")
        return "Charts not found.", 404
    except Exception:
        logger.exception("Failed to create JSON file.")
        return "Failed to create JSON file.", 500


def _add_chart_popup():
    """Render the add chart popup form."""
    return render_template("admins/owid_charts/add.html")


def _add_chart() -> ResponseReturnValue:
    """Create a new chart from the submitted form data."""
    from_popup = request.form.get("from_popup") == "1"

    slug = request.form.get("slug", "").strip()
    title = request.form.get("title", "").strip()

    if not slug or not title:
        flash("Slug and Title are required.", "danger")
        if from_popup:
            return redirect(url_for("admin.owidcharts.add_chart"))
        return redirect(url_for("admin.owidcharts.dashboard"))

    has_map_tab = 1 if request.form.get("has_map_tab") == "on" else 0
    is_published = 1 if request.form.get("is_published") == "on" else 0
    single_year_data = 1 if request.form.get("single_year_data") == "1" else 0
    has_timeline = 1 if request.form.get("has_timeline") == "1" else 0

    max_time = request.form.get("max_time", type=int)
    min_time = request.form.get("min_time", type=int)
    default_tab = request.form.get("default_tab", "").strip()
    len_years = request.form.get("len_years", type=int)

    save_error = None
    try:
        record = owid_charts_service.add_chart(
            slug=slug,
            title=title,
            has_map_tab=has_map_tab,
            max_time=max_time,
            min_time=min_time,
            default_tab=default_tab or None,
            is_published=is_published,
            single_year_data=single_year_data,
            len_years=len_years,
            has_timeline=has_timeline,
        )
    except ValueError as exc:
        logger.exception("Unable to add chart.")
        flash(str(exc), "warning")
        save_error = True
    except IntegrityError:
        logger.exception("Unable to add chart.")
        flash("Chart with this slug already exists.", "danger")
        save_error = True
    except Exception:
        logger.exception("Unable to add chart.")
        flash("Unable to add chart. Please try again.", "danger")
        save_error = True
    else:
        flash(f"Chart '{record.title}' added.", "success")

    if from_popup and save_error:
        return redirect(url_for("admin.owidcharts.add_chart_popup"))

    if from_popup:
        return render_template("admins/popup_action.html")
    return redirect(url_for("admin.owidcharts.dashboard"))


def _update_chart() -> ResponseReturnValue:
    """Update a chart from the submitted form data."""
    from_popup = request.form.get("from_popup") == "1"

    chart_id = request.form.get("chart_id", default=0, type=int)

    slug = request.form.get("slug", "").strip()
    title = request.form.get("title", "").strip()

    if not slug or not title:
        flash("Slug and Title are required.", "danger")
        if from_popup:
            return redirect(url_for("admin.owidcharts.edit_chart", chart_id=chart_id))
        return redirect(url_for("admin.owidcharts.dashboard"))

    has_map_tab = request.form.get("has_map_tab") == "on"
    max_time = request.form.get("max_time", type=int)
    min_time = request.form.get("min_time", type=int)
    default_tab = request.form.get("default_tab", "").strip()
    is_published = request.form.get("is_published") == "on"
    single_year_data = request.form.get("single_year_data") == "1"
    len_years = request.form.get("len_years", type=int)
    has_timeline = request.form.get("has_timeline") == "1"

    save_error = None
    chart_data = {
        "slug": slug,
        "title": title,
        "has_map_tab": has_map_tab,
        "max_time": max_time,
        "min_time": min_time,
        "default_tab": default_tab,
        "is_published": is_published,
        "single_year_data": single_year_data,
        "len_years": len_years,
        "has_timeline": has_timeline,
    }
    try:
        record = owid_charts_service.update_chart_data(
            chart_id=chart_id,
            chart_data=chart_data,
        )
    except LookupError as exc:
        logger.exception("Unable to update chart.")
        flash(str(exc), "warning")
        save_error = True
    except ValueError as exc:
        logger.exception("Unable to update chart.")
        flash(str(exc), "warning")
        save_error = True
    except Exception:
        logger.exception("Unable to update chart.")
        flash("Unable to update chart. Please try again.", "danger")
        save_error = True
    else:
        flash(f"Chart '{record.title}' updated.", "success")

    if from_popup and save_error:
        return redirect(url_for("admin.owidcharts.edit_chart", chart_id=chart_id))

    if from_popup:
        return render_template("admins/popup_action.html")
    return redirect(url_for("admin.owidcharts.dashboard"))


def _delete_chart(chart_id: int) -> ResponseReturnValue:
    """Remove a chart entirely."""
    from_popup = request.form.get("from_popup") == "1"

    try:
        record = owid_charts_service.delete_chart(chart_id)
    except LookupError as exc:
        logger.exception("Unable to delete chart.")
        flash(str(exc), "warning")
    except Exception:
        logger.exception("Unable to delete chart.")
        flash("Unable to delete chart. Please try again.", "danger")
    else:
        flash(f"Chart '{record.title}' removed.", "success")

    if from_popup:
        return render_template("admins/popup_action.html")
    return redirect(url_for("admin.owidcharts.dashboard"))


def _edit_chart(chart_id: int) -> ResponseReturnValue:
    """Render the edit chart popup page."""
    try:
        chart = owid_charts_service.get_chart_by_id(chart_id)
    except LookupError:
        return render_template(
            "admins/owid_charts/edit.html",
            error="Chart not found",
            chart=None,
        )

    return render_template(
        "admins/owid_charts/edit.html",
        chart=chart,
        error=None,
    )


class OwidCharts:
    def __init__(self):
        self.bp = Blueprint("owidcharts", __name__, url_prefix="/owidcharts")
        self._setup_routes()

    def _setup_routes(self):
        @self.bp.get("/")
        @self.bp.get("/<string:template_filter>")
        @admin_required
        def dashboard(template_filter: str = ""):
            return render_template("admins/owid_charts/list.html", selected_template=template_filter)

        @self.bp.get("/add")
        @admin_required
        def add_chart_popup() -> ResponseReturnValue:
            return _add_chart_popup()

        @self.bp.post("/add")
        @admin_required
        def add_chart() -> ResponseReturnValue:
            return _add_chart()

        @self.bp.post("/update")
        @admin_required
        def update_chart_data() -> ResponseReturnValue:
            chart_id = request.form.get("chart_id", default=0, type=int)
            from_popup = request.form.get("from_popup") == "1"

            if not chart_id:
                flash("Chart ID is required.", "danger")
                if from_popup:
                    return redirect(url_for("admin.owidcharts.edit_chart", chart_id=chart_id))
                return redirect(url_for("admin.owidcharts.dashboard"))

            return _update_chart()

        @self.bp.post("/<int:chart_id>/delete")
        @admin_required
        def delete_chart(chart_id: int) -> ResponseReturnValue:
            return _delete_chart(chart_id)

        @self.bp.get("/<int:chart_id>/edit")
        @admin_required
        def edit_chart(chart_id: int) -> ResponseReturnValue:
            return _edit_chart(chart_id)

        @self.bp.get("/download-json")
        @admin_required
        def download_owid_charts_json() -> ResponseReturnValue:
            """Download all charts as a JSON file."""
            response, status_code = create_json_file()

            if status_code != 200:
                flash(response, "warning" if status_code == 404 else "danger")
                return redirect(url_for("admin.owidcharts.dashboard"))

            return response


owidcharts_module = OwidCharts()

__all__ = [
    "owidcharts_module",
]
