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

from ...db.services import users_service
from ..decorators import admin_required

logger = logging.getLogger(__name__)


def _dashboard() -> str:
    """Render the user management dashboard."""
    try:
        users = users_service.list_users()
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


def _update_can_run_jobs(user_id: int, desired: int) -> ResponseReturnValue:
    """Toggle the can_run_jobs column for a user."""

    try:
        record = users_service.toggle_can_run_jobs(user_id, bool(desired))
    except LookupError:
        logger.exception("Unable to update user permissions.")
        flash(f"User with id {user_id} was not found", "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to update user permissions.")
        flash("Unable to update user permissions. Please try again.", "danger")
    else:
        flash(f"User '{record.username}' permissions updated.", "success")
        logger.info(f"User '{record.username}' [can_run_jobs]={desired} updated.")

    return redirect(url_for("admin.users.dashboard"))


def _update_can_run_bg_jobs(user_id: int, desired: int) -> ResponseReturnValue:
    """Toggle the can_run_bg_jobs column for a user."""

    try:
        record = users_service.toggle_can_run_bg_jobs(user_id, bool(desired))
    except LookupError:
        logger.exception("Unable to update user permissions.")
        flash(f"User with id {user_id} was not found", "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to update user permissions.")
        flash("Unable to update user permissions. Please try again.", "danger")
    else:
        flash(f"User '{record.username}' permissions updated.", "success")
        logger.info(f"User '{record.username}' [can_run_bg_jobs]={desired} updated.")

    return redirect(url_for("admin.users.dashboard"))


class UsersRoutes:
    """Jobs management routes."""

    def __init__(self) -> None:
        self.bp = Blueprint("users", __name__, url_prefix="/users")
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        @admin_required
        def dashboard():
            return _dashboard()

        @self.bp.post("/<int:user_id>/can_run_jobs")
        @admin_required
        def update_can_run_jobs(user_id: int) -> ResponseReturnValue:
            desired = 1 if request.form.get("can_run_jobs", "0") == "1" else 0
            return _update_can_run_jobs(user_id, desired)

        @self.bp.post("/<int:user_id>/can_run_bg_jobs")
        @admin_required
        def update_can_run_bg_jobs(user_id: int) -> ResponseReturnValue:
            desired = 1 if request.form.get("can_run_bg_jobs", "0") == "1" else 0
            return _update_can_run_bg_jobs(user_id, desired)


users_module = UsersRoutes()

__all__ = [
    "users_module",
]
