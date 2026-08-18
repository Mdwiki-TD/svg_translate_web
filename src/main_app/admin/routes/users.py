""" """

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

from ...database.services import UsersService
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class UsersRoutes:
    """Jobs management routes."""

    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self.user_service = UsersService()
        self._setup_routes()

    def _setup_routes(self) -> None:

        routes = [
            ("/", "GET", self.dashboard),
            ("/<int:user_id>/can_run_jobs", "POST", self.update_can_run_jobs),
            ("/<int:user_id>/can_run_bg_jobs", "POST", self.update_can_run_bg_jobs),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(admin_required(target))

    def dashboard(self) -> str:
        """Render the user management dashboard."""
        try:
            users = self.user_service.list_users()
        except Exception as e:  # pragma: no cover - defensive guard
            logger.error(f"Error listing users: {e}")
            flash("Error listing users", "error")
            users: list[Any] = []

        total = len(users)

        return render_template(
            "admins/users.html",
            users=users,
            total_users=total,
        )

    def update_can_run_jobs(self, user_id: int) -> ResponseReturnValue:
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

    def update_can_run_bg_jobs(self, user_id: int) -> ResponseReturnValue:
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


__all__ = [
    "UsersRoutes",
]
