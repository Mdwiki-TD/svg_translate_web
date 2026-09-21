"""Slug Redirects administration routes rendered as MethodView classes."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from flask.views import MethodView

from ...database.services import OwidSlugRedirectsService
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class SlugDashboardView(MethodView):
    """View to render the slug redirects dashboard."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.service = OwidSlugRedirectsService()

    def get(self) -> str:
        """Render the slug redirects dashboard with summary counts."""
        records = self.service.list_slug_redirects()
        total = len(records)  # count_slug_redirects()
        total_should_be_replaced = len([r for r in records if r.should_be_replaced])
        total_should_not_be_replaced = total - total_should_be_replaced

        return render_template(
            "admins/slug_redirects/list.html",
            records=records,
            total=total,
            total_should_be_replaced=total_should_be_replaced,
            total_should_not_be_replaced=total_should_not_be_replaced,
        )


class EditSlugRedirectView(MethodView):
    """View to render the edit slug redirect popup page."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.service = OwidSlugRedirectsService()

    def get(self, redirect_id: int) -> ResponseReturnValue:
        """Render the edit form for a single slug redirect."""
        record = self.service.get_slug_redirect_by_id(redirect_id)
        if not record:
            return render_template(
                "admins/slug_redirects/edit.html",
                error="Redirect record not found",
                record=None,
            )

        return render_template(
            "admins/slug_redirects/edit.html",
            record=record,
            error=None,
        )


class UpdateSlugRedirectDataView(MethodView):
    """View to apply a slug redirect update submitted from the edit form."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.service = OwidSlugRedirectsService()

    def post(self) -> ResponseReturnValue:
        """Update a single slug redirect and redirect back to the dashboard."""
        redirect_id = request.form.get("id", type=int)
        from_popup = request.form.get("from_popup") == "1"
        should_be_replaced = request.form.get("should_be_replaced") == "on"

        if not redirect_id:
            flash("Redirect ID is required.", "danger")
            return redirect(url_for("adminpanel.slugredirects.dashboard"))

        if self.service.update_slug_redirect(redirect_id, {"should_be_replaced": should_be_replaced}):
            flash("Slug redirect updated.", "success")
        else:
            flash("Slug redirect not found.", "danger")

        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("adminpanel.slugredirects.dashboard"))


class DeleteSlugRedirectDataView(MethodView):
    """View to delete a single slug redirect."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.service = OwidSlugRedirectsService()

    def post(self, redirect_id: int) -> ResponseReturnValue:
        """Delete the slug redirect with the given id."""
        if self.service.delete(redirect_id):
            flash("Slug redirect deleted.", "success")
        else:
            flash("Slug redirect not found.", "danger")
        return redirect(url_for("adminpanel.slugredirects.dashboard"))


class SlugBulkActionView(MethodView):
    """View to apply a bulk action to the selected slug redirects."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.service = OwidSlugRedirectsService()

    def post(self) -> ResponseReturnValue:
        """Apply the requested bulk action to the selected redirect ids."""
        action = request.form.get("action")
        selected_ids = request.form.getlist("selected_ids", type=int)

        if not selected_ids:
            flash("No items selected.", "warning")
            return redirect(url_for("adminpanel.slugredirects.dashboard"))
        try:
            if action == "mark_replace":
                self.service.bulk_update_slug_redirects(selected_ids, {"should_be_replaced": True})
                flash(f"Marked {len(selected_ids)} redirects as 'replace'.", "success")
            elif action == "mark_no_replace":
                self.service.bulk_update_slug_redirects(selected_ids, {"should_be_replaced": False})
                flash(f"Marked {len(selected_ids)} redirects as 'do not replace'.", "success")
            elif action == "delete":
                self.service.bulk_delete_slug_redirects(selected_ids)
                flash(f"Deleted {len(selected_ids)} redirects.", "success")
            else:
                flash("Invalid action.", "danger")
        except Exception:
            logger.error("Error in bulk action")
            flash("An error occurred.", "danger")

        return redirect(url_for("adminpanel.slugredirects.dashboard"))


class SlugRedirectsRoutes:
    """Registrar class to bind admin slug redirect MethodViews to a Blueprint."""

    def register(self, bp: Blueprint) -> None:
        """Register admin slug redirect URL rules on the provided blueprint with admin protection."""
        bp.add_url_rule("/", view_func=SlugDashboardView.as_view("dashboard"))
        bp.add_url_rule(
            "/<int:redirect_id>/edit",
            view_func=EditSlugRedirectView.as_view("edit_slug_redirect"),
        )
        bp.add_url_rule(
            "/update",
            view_func=UpdateSlugRedirectDataView.as_view("update_slug_redirect_data"),
        )
        bp.add_url_rule(
            "/<int:redirect_id>/delete",
            view_func=DeleteSlugRedirectDataView.as_view("delete_slug_redirect_data"),
        )
        bp.add_url_rule(
            "/bulk_action",
            view_func=SlugBulkActionView.as_view("bulk_action"),
        )


__all__ = [
    "SlugRedirectsRoutes",
]
