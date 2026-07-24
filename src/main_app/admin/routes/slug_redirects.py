"""Slug Redirects administration routes."""

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

from ...db.services import (
    OwidSlugRedirectsService,
    bulk_delete_slug_redirects,
    bulk_update_slug_redirects,
    get_slug_redirect_by_id,
    list_slug_redirects,
    update_slug_redirect,
)
from ..decorators import admin_required

logger = logging.getLogger(__name__)


def delete_slug_redirect(record_id):
    return OwidSlugRedirectsService().delete(record_id)


def _edit_slug_redirect(redirect_id: int) -> ResponseReturnValue:
    """Render the edit slug redirect popup page."""
    record = get_slug_redirect_by_id(redirect_id)
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


class SlugFuncs:
    def __init__(self) -> None:
        self.service = OwidSlugRedirectsService()

    def dashboard(self):
        records = list_slug_redirects()
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

    def edit_slug_redirect(self, redirect_id: int) -> ResponseReturnValue:
        return _edit_slug_redirect(redirect_id)

    def update_slug_redirect_data(self) -> ResponseReturnValue:
        redirect_id = request.form.get("id", type=int)
        from_popup = request.form.get("from_popup") == "1"
        should_be_replaced = request.form.get("should_be_replaced") == "on"

        if not redirect_id:
            flash("Redirect ID is required.", "danger")
            return redirect(url_for("adminpanel.slugredirects.dashboard"))

        if update_slug_redirect(redirect_id, {"should_be_replaced": should_be_replaced}):
            flash("Slug redirect updated.", "success")
        else:
            flash("Slug redirect not found.", "danger")

        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("adminpanel.slugredirects.dashboard"))

    def delete_slug_redirect_data(self, redirect_id: int) -> ResponseReturnValue:
        if delete_slug_redirect(redirect_id):
            flash("Slug redirect deleted.", "success")
        else:
            flash("Slug redirect not found.", "danger")
        return redirect(url_for("adminpanel.slugredirects.dashboard"))

    def bulk_action(self) -> ResponseReturnValue:
        action = request.form.get("action")
        selected_ids = request.form.getlist("selected_ids", type=int)

        if not selected_ids:
            flash("No items selected.", "warning")
            return redirect(url_for("adminpanel.slugredirects.dashboard"))
        try:
            if action == "mark_replace":
                bulk_update_slug_redirects(selected_ids, {"should_be_replaced": True})
                flash(f"Marked {len(selected_ids)} redirects as 'replace'.", "success")
            elif action == "mark_no_replace":
                bulk_update_slug_redirects(selected_ids, {"should_be_replaced": False})
                flash(f"Marked {len(selected_ids)} redirects as 'do not replace'.", "success")
            elif action == "delete":
                bulk_delete_slug_redirects(selected_ids)
                flash(f"Deleted {len(selected_ids)} redirects.", "success")
            else:
                flash("Invalid action.", "danger")
        except Exception:
            logger.error("Error in bulk action")
            flash("An error occurred.", "danger")

        return redirect(url_for("adminpanel.slugredirects.dashboard"))


class SlugRedirectsRoutes(SlugFuncs):
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        super().__init__()
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.route("/", methods=["GET"])(admin_required(self.dashboard))
        self.bp.route("/<int:redirect_id>/edit", methods=["GET"])(admin_required(self.edit_slug_redirect))
        self.bp.route("/update", methods=["POST"])(admin_required(self.update_slug_redirect_data))
        self.bp.route("/<int:redirect_id>/delete", methods=["POST"])(admin_required(self.delete_slug_redirect_data))
        self.bp.route("/bulk_action", methods=["POST"])(admin_required(self.bulk_action))


__all__ = [
    "SlugRedirectsRoutes",
]
