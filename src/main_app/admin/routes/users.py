"""Admin user management routes rendered as MethodView classes."""

from __future__ import annotations

import logging
from typing import Any

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

from ...database.services import UsersService
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class UsersDashboardView(MethodView):
    """View to render the user management dashboard."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.user_service = UsersService()

    def get(self) -> str:
        """Render the user management dashboard."""
        try:
            users = self.user_service.list_users()
        except Exception as e:  # pragma: no cover - defensive guard
            logger.error("Error listing users: %s", e)
            flash("Error listing users", "error")
            users: list[Any] = []

        total = len(users)

        return render_template(
            "admins/users.html",
            users=users,
            total_users=total,
        )


class UpdateCanRunJobsView(MethodView):
    """View to toggle the can_run_jobs column for a user."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.user_service = UsersService()

    def post(self, user_id: int) -> ResponseReturnValue:
        """Toggle the can_run_jobs column for a user."""
        desired = 1 if request.form.get("can_run_jobs", "0") == "1" else 0
        try:
            record = self.user_service.toggle_can_run_jobs(user_id, bool(desired))
        except LookupError:
            logger.exception("Unable to update user permissions.")
            flash(f"User with id {user_id} was not found", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to update user permissions.")
            flash("Unable to update user permissions. Please try again.", "danger")
        else:
            if record is None:
                flash("Unable to update user permissions. Please try again.", "danger")
            else:
                flash(f"User '{record.username}' permissions updated.", "success")
                logger.info(f"User '{record.username}' [can_run_jobs]={desired} updated.")

        return redirect(url_for("adminpanel.users.dashboard"))


class UpdateCanRunBgJobsView(MethodView):
    """View to toggle the can_run_bg_jobs column for a user."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.user_service = UsersService()

    def post(self, user_id: int) -> ResponseReturnValue:
        """Toggle the can_run_bg_jobs column for a user."""
        desired = 1 if request.form.get("can_run_bg_jobs", "0") == "1" else 0

        try:
            record = self.user_service.toggle_can_run_bg_jobs(user_id, bool(desired))
        except LookupError:
            logger.exception("Unable to update user permissions.")
            flash(f"User with id {user_id} was not found", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to update user permissions.")
            flash("Unable to update user permissions. Please try again.", "danger")
        else:
            if record is None:
                flash("Unable to update user permissions. Please try again.", "danger")
            else:
                flash(f"User '{record.username}' permissions updated.", "success")
                logger.info(f"User '{record.username}' [can_run_bg_jobs]={desired} updated.")

        return redirect(url_for("adminpanel.users.dashboard"))


class UsersRoutes:
    """Registrar class to bind admin users MethodViews to a Blueprint."""

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register the dashboard and the two permission-toggle endpoints."""
        bp.add_url_rule(
            "/",
            view_func=UsersDashboardView.as_view("dashboard"),
            methods=["GET"],
        )
        bp.add_url_rule(
            "/<int:user_id>/can_run_jobs",
            view_func=UpdateCanRunJobsView.as_view("update_can_run_jobs"),
            methods=["POST"],
        )
        bp.add_url_rule(
            "/<int:user_id>/can_run_bg_jobs",
            view_func=UpdateCanRunBgJobsView.as_view("update_can_run_bg_jobs"),
            methods=["POST"],
        )

    # ----------------------------------------------------------------------
    # TODO: Backward Compatibility
    # Legacy handler methods kept so callers/tests that invoked them
    # directly on the registrar still work. Remove once all consumers
    # use the MethodView classes above.
    # ----------------------------------------------------------------------
    def dashboard(self) -> str:
        """Render the user management dashboard."""
        return UsersDashboardView().get()

    def update_can_run_jobs(self, user_id: int) -> ResponseReturnValue:
        """Toggle the can_run_jobs column for a user."""
        return UpdateCanRunJobsView().post(user_id)

    def update_can_run_bg_jobs(self, user_id: int) -> ResponseReturnValue:
        """Toggle the can_run_bg_jobs column for a user."""
        return UpdateCanRunBgJobsView().post(user_id)


__all__ = [
    "UsersRoutes",
]
