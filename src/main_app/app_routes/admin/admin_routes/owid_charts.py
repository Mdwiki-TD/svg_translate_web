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

from ....services import owid_charts_service
from ....admins.admins_required import admin_required
from ....db import OwidChartRecord
from ....users.current import current_user

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

        if not charts:
            return "No charts found to export.", 404

        charts_data = [
            {
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
                "template_id": chart.template_id,
                "template_title": chart.template_title,
                "template_source": chart.template_source,
            }
            for chart in charts
        ]

        json_content = json.dumps(charts_data, indent=2, ensure_ascii=False)

        response = make_response(json_content)
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Disposition"] = "attachment; filename=owid_charts.json"

        return response, 200

    except LookupError as exc:
        logger.exception("Charts not found.")
        return f"Charts not found: {exc}", 404
    except Exception as exc:
        logger.exception("Failed to create JSON file.")
        return f"Failed to create JSON file: {exc}", 500


def _charts_dashboard():
    """Render the charts management dashboard."""
    user = current_user()
    template_filter = request.args.get("template", "").strip()
    all_charts: List[OwidChartRecord] = owid_charts_service.list_charts()

    if template_filter == "has_template":
        charts = [c for c in all_charts if c.template_title]
    elif template_filter == "no_template":
        charts = [c for c in all_charts if not c.template_title]
    else:
        charts = all_charts

    total = len(all_charts)
    all_charts_summary = {
        "total": total,
        "published": {
            "with": len([c for c in all_charts if c.is_published]),
            "without": len([c for c in all_charts if not c.is_published]),
        },
        "template": {
            "with": len([c for c in all_charts if c.template_id]),
            "without": len([c for c in all_charts if not c.template_id]),
        },
        "map_tab": {
            "with": len([c for c in all_charts if c.has_map_tab]),
            "without": len([c for c in all_charts if not c.has_map_tab]),
        },
        "timeline": {
            "with": len([c for c in all_charts if c.has_timeline]),
            "without": len([c for c in all_charts if not c.has_timeline]),
        },
    }

    return render_template(
        "admins/owid_charts/list.html",
        current_user=user,
        charts=charts,
        total_charts=total,
        all_charts_summary=all_charts_summary,
        selected_template=template_filter,
    )


def _add_chart_popup():
    """Render the add chart popup form."""
    return render_template("admins/owid_charts/add.html")


def _add_chart() -> ResponseReturnValue:
    """Create a new chart from the submitted form data."""
    slug = request.form.get("slug", "").strip()
    title = request.form.get("title", "").strip()

    if not slug or not title:
        flash("Slug and Title are required.", "danger")
        return redirect(url_for("admin.owid_charts_dashboard"))

    has_map_tab = request.form.get("has_map_tab") == "on"
    max_time = request.form.get("max_time", type=int)
    min_time = request.form.get("min_time", type=int)
    default_tab = request.form.get("default_tab", "").strip()
    is_published = request.form.get("is_published") == "on"
    single_year_data = request.form.get("single_year_data") == "1"
    len_years = request.form.get("len_years", type=int)
    has_timeline = request.form.get("has_timeline") == "1"

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
    except Exception:
        logger.exception("Unable to add chart.")
        flash("Unable to add chart. Please try again.", "danger")
    else:
        flash(f"Chart '{record.title}' added.", "success")

    return redirect(url_for("admin.owid_charts_dashboard"))


def _update_chart() -> ResponseReturnValue:
    """Update a chart from the submitted form data."""
    chart_id = request.form.get("chart_id", default=0, type=int)
    from_popup = request.form.get("from_popup") == "1"

    if not chart_id:
        flash("Chart ID is required.", "danger")
        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("admin.owid_charts_dashboard"))

    slug = request.form.get("slug", "").strip()
    title = request.form.get("title", "").strip()

    if not slug or not title:
        flash("Slug and Title are required.", "danger")
        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("admin.owid_charts_dashboard"))

    has_map_tab = request.form.get("has_map_tab") == "on"
    max_time = request.form.get("max_time", type=int)
    min_time = request.form.get("min_time", type=int)
    default_tab = request.form.get("default_tab", "").strip()
    is_published = request.form.get("is_published") == "on"
    single_year_data = request.form.get("single_year_data") == "1"
    len_years = request.form.get("len_years", type=int)
    has_timeline = request.form.get("has_timeline") == "1"

    try:
        record = owid_charts_service.update_chart(
            chart_id=chart_id,
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
    except LookupError as exc:
        logger.exception("Unable to update chart.")
        flash(str(exc), "warning")
    except Exception:
        logger.exception("Unable to update chart.")
        flash("Unable to update chart. Please try again.", "danger")
    else:
        flash(f"Chart '{record.title}' updated.", "success")

    if from_popup:
        return render_template("admins/popup_action.html")
    return redirect(url_for("admin.owid_charts_dashboard"))


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
    return redirect(url_for("admin.owid_charts_dashboard"))


def _edit_chart(chart_id: int) -> ResponseReturnValue:
    """Render the edit chart popup page."""
    try:
        chart = owid_charts_service.get_chart(chart_id)
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
    def __init__(self, bp_admin: Blueprint):
        @bp_admin.get("/owid-charts")
        @admin_required
        def owid_charts_dashboard():
            return _charts_dashboard()

        @bp_admin.get("/owid-charts/add")
        @admin_required
        def add_chart_popup() -> ResponseReturnValue:
            return _add_chart_popup()

        @bp_admin.post("/owid-charts/add")
        @admin_required
        def add_chart() -> ResponseReturnValue:
            return _add_chart()

        @bp_admin.post("/owid-charts/update")
        @admin_required
        def update_chart() -> ResponseReturnValue:
            return _update_chart()

        @bp_admin.post("/owid-charts/<int:chart_id>/delete")
        @admin_required
        def delete_chart(chart_id: int) -> ResponseReturnValue:
            return _delete_chart(chart_id)

        @bp_admin.get("/owid-charts/<int:chart_id>/edit")
        @admin_required
        def edit_chart(chart_id: int) -> ResponseReturnValue:
            return _edit_chart(chart_id)

        @bp_admin.get("/owid-charts/download-json")
        @admin_required
        def download_owid_charts_json() -> ResponseReturnValue:
            """Download all charts as a JSON file."""
            response, status_code = create_json_file()

            if status_code != 200:
                flash(response, "warning" if status_code == 404 else "danger")
                return redirect(url_for("admin.owid_charts_dashboard"))

            return response
