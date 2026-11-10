"""OWID Charts administration routes rendered as MethodView classes."""

from __future__ import annotations

import json
import logging
from typing import Any

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
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError
from werkzeug.datastructures import ImmutableMultiDict

from ...database.services import ChartAndTemplate, ChartsAndTemplatesService, OwidChartsService
from ...services.owid_charts_utils import make_charts_summary
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class OwidCharts:
    """Shared helpers used by the admin OWID charts MethodViews."""

    def __init__(self) -> None:
        self.owid_charts_service = OwidChartsService()
        self.charts_and_tmps_service = ChartsAndTemplatesService()

    def create_json_file(self) -> tuple[Any, int]:
        """Create a JSON file containing all charts data.

        Returns:
            Tuple of (response, status_code) where response is either a Flask
            response object for file download (status 200) or an error message
            string with appropriate status code (404 for no charts, 500 for errors).
        """
        try:
            # Optimize: use single-query list_all() to fetch charts and template relationships
            charts_with_templates: list[ChartAndTemplate] = self.charts_and_tmps_service.list_all()

            if not charts_with_templates:
                return "No charts found to export.", 404

            charts_data: list[dict[str, Any]] = [x.to_dict_joined() for x in charts_with_templates]

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

    def dashboard(self, template_filter: str = "") -> str:
        """Render the admin charts list, optionally filtered by template."""
        # Optimize: use single-query list_all() with fallback
        charts_with_templates: list[ChartAndTemplate] = self.charts_and_tmps_service.list_all()

        summary = make_charts_summary(charts_with_templates)

        charts_data: list[dict[str, Any]] = [x.to_dict_joined(template_filter) for x in charts_with_templates]
        rows = [x for x in charts_data if x]
        return render_template(
            "admins/owid_charts/list.html",
            selected_template=template_filter,
            summary=summary,
            rows=rows,
            show_map_and_timeline=False,
        )

    def _add_chart(self, request_form: dict[str, Any] | ImmutableMultiDict) -> ResponseReturnValue:
        """Create a new chart from the submitted form data."""
        if isinstance(request_form, dict):
            request_form = ImmutableMultiDict(request_form)

        from_popup = request_form.get("from_popup") == "1"

        slug = request_form.get("slug", "").strip()
        title = request_form.get("title", "").strip()

        if not slug or not title:
            flash("Slug and Title are required.", "danger")
            if from_popup:
                return redirect(url_for("adminpanel.owidcharts.add_chart_popup"))
            return redirect(url_for("adminpanel.owidcharts.dashboard"))

        has_map_tab = 1 if request_form.get("has_map_tab") == "on" else 0
        is_published = 1 if request_form.get("is_published") == "on" else 0
        single_year_data = 1 if request_form.get("single_year_data") == "1" else 0
        has_timeline = 1 if request_form.get("has_timeline") == "1" else 0

        max_time = request_form.get("max_time", type=int)
        min_time = request_form.get("min_time", type=int)
        default_tab = request_form.get("default_tab", "").strip()
        len_years = request_form.get("len_years", type=int)

        save_error = None
        try:
            record = self.owid_charts_service.add_chart(
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
        except ValueError:
            logger.exception("Unable to add chart.")
            flash("Unable to add chart.", "danger")
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
            flash(f"Chart '{title}' added.", "success")

        if from_popup and save_error:
            return redirect(url_for("adminpanel.owidcharts.add_chart_popup"))

        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("adminpanel.owidcharts.dashboard"))

    def _update_chart(self, request_form: dict[str, Any] | ImmutableMultiDict) -> ResponseReturnValue:
        """Update a chart from the submitted form data."""
        if isinstance(request_form, dict):
            request_form = ImmutableMultiDict(request_form)

        from_popup = request_form.get("from_popup") == "1"

        chart_id = request_form.get("chart_id", default=0, type=int)

        slug = request_form.get("slug", "").strip()
        title = request_form.get("title", "").strip()

        if not slug or not title:
            flash("Slug and Title are required.", "danger")
            if from_popup:
                return redirect(url_for("adminpanel.owidcharts.edit_chart", chart_id=chart_id))
            return redirect(url_for("adminpanel.owidcharts.dashboard"))

        has_map_tab = request_form.get("has_map_tab") == "on"
        max_time = request_form.get("max_time", type=int)
        min_time = request_form.get("min_time", type=int)
        default_tab = request_form.get("default_tab", "").strip()
        is_published = request_form.get("is_published") == "on"
        single_year_data = request_form.get("single_year_data") == "1"
        len_years = request_form.get("len_years", type=int)
        has_timeline = request_form.get("has_timeline") == "1"

        save_error = None
        chart_data = {
            "slug": slug,
            "title": title,
            "has_map_tab": has_map_tab,
            "max_time": max_time,
            "min_time": min_time,
            "default_tab": default_tab or None,
            "is_published": is_published,
            "single_year_data": single_year_data,
            "len_years": len_years,
            "has_timeline": has_timeline,
        }
        try:
            record = self.owid_charts_service.update_chart_data(
                chart_id=chart_id,
                chart_data=chart_data,
            )
        except LookupError:
            logger.exception("Unable to update chart.")
            flash(f"Chart with id {chart_id} was not found", "warning")
            save_error = True
        except ValueError:
            logger.exception("Unable to update chart.")
            flash("Unable to update chart.", "danger")
            save_error = True
        except Exception:
            logger.exception("Unable to update chart.")
            flash("Unable to update chart. Please try again.", "danger")
            save_error = True
        else:
            if record:
                flash(f"Chart '{record.title}' updated.", "success")
            else:
                flash(f"Chart '{chart_id}' not found.", "warning")

        if from_popup and save_error:
            return redirect(url_for("adminpanel.owidcharts.edit_chart", chart_id=chart_id))

        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("adminpanel.owidcharts.dashboard"))

    def _delete_chart(self, chart_id: int, from_popup: bool) -> ResponseReturnValue:
        """Remove a chart entirely."""

        try:
            if self.owid_charts_service.delete(chart_id):
                flash(f"Chart '{chart_id}' removed.", "success")
            else:
                flash(f"Chart '{chart_id}' not found.", "warning")
        except Exception:
            logger.exception("Unable to delete chart.")
            flash("Unable to delete chart. Please try again.", "danger")

        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("adminpanel.owidcharts.dashboard"))

    def _edit_chart(self, chart_id: int) -> ResponseReturnValue:
        """Render the edit chart popup page."""
        chart = self.owid_charts_service.get_chart_by_id(chart_id)
        if not chart:
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


class OwidChartsDashboardView(OwidCharts, MethodView):
    """View to render the admin OWID charts list, with or without a template filter."""

    decorators = [admin_required]

    def get(self, template_filter: str = "") -> str:
        """Render the charts list filtered by the optional template."""
        return self.dashboard(template_filter)


class AddChartPopupView(OwidCharts, MethodView):
    """View to render the add chart popup form."""

    decorators = [admin_required]

    def get(self) -> ResponseReturnValue:
        """Render the add chart popup form."""
        return render_template("admins/owid_charts/add.html")


class AddChartView(OwidCharts, MethodView):
    """View to create a chart from the add popup form."""

    decorators = [admin_required]

    def post(self) -> ResponseReturnValue:
        """Create a new chart from the submitted form data."""
        return self._add_chart(request.form)


class EditChartView(OwidCharts, MethodView):
    """View to render the edit chart popup page by id."""

    decorators = [admin_required]

    def get(self, chart_id: int) -> ResponseReturnValue:
        """Render the edit chart popup page for the given id."""
        return self._edit_chart(chart_id)


class UpdateChartView(OwidCharts, MethodView):
    """View to apply a chart update submitted from the edit form."""

    decorators = [admin_required]

    def post(self) -> ResponseReturnValue:
        """Update the chart identified by the submitted form chart_id."""
        chart_id = request.form.get("chart_id", default=0, type=int)
        from_popup = request.form.get("from_popup") == "1"

        if not chart_id:
            flash("Chart ID is required.", "danger")
            if from_popup:
                return redirect(url_for("adminpanel.owidcharts.edit_chart", chart_id=chart_id))
            return redirect(url_for("adminpanel.owidcharts.dashboard"))

        return self._update_chart(request.form)


class DeleteChartView(OwidCharts, MethodView):
    """View to delete a single chart."""

    decorators = [admin_required]

    def post(self, chart_id: int) -> ResponseReturnValue:
        """Remove the chart with the given id."""
        from_popup = request.form.get("from_popup") == "1"
        return self._delete_chart(chart_id, from_popup)


class DownloadOwidChartsJsonView(OwidCharts, MethodView):
    """View to download all charts as a JSON file."""

    decorators = [admin_required]

    def get(self) -> ResponseReturnValue:
        """Download all charts as a json file."""
        response, status_code = self.create_json_file()

        if status_code != 200:
            flash(response, "warning" if status_code == 404 else "danger")
            return redirect(url_for("adminpanel.owidcharts.dashboard"))

        return response


class OwidChartsRoutes(OwidCharts):
    """Registrar class to bind admin OWID charts MethodViews to a Blueprint."""

    def __init__(self) -> None:
        self.name = "owidcharts"
        super().__init__()

    def register(self, bp: Blueprint) -> None:
        """Register admin OWID charts URL rules on the provided blueprint with admin protection."""
        # One view serves both the unfiltered list and the filtered list, which
        # keeps a distinct endpoint name for url_for(..., template_filter=...)
        dashboard_view = OwidChartsDashboardView.as_view("dashboard")
        bp.add_url_rule("/", view_func=dashboard_view)
        bp.add_url_rule(
            "/<string:template_filter>",
            endpoint="dashboard_with_filter",
            view_func=dashboard_view,
        )

        # GET renders the popup form, POST persists the new chart
        bp.add_url_rule("/add", view_func=AddChartPopupView.as_view("add_chart_popup"), methods=["GET"])
        bp.add_url_rule("/add", view_func=AddChartView.as_view("add_chart"), methods=["POST"])

        bp.add_url_rule(
            "/<int:chart_id>/edit",
            view_func=EditChartView.as_view("edit_chart"),
        )
        bp.add_url_rule(
            "/download-json",
            view_func=DownloadOwidChartsJsonView.as_view("download_owid_charts_json"),
        )
        bp.add_url_rule("/update", view_func=UpdateChartView.as_view("update_chart"))
        bp.add_url_rule(
            "/<int:chart_id>/delete",
            view_func=DeleteChartView.as_view("delete_chart"),
        )


__all__ = [
    "OwidChartsRoutes",
]
