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

from ...db.exceptions import DuplicateUserError, UserNotFoundError
from ...db.services import (
    add_coordinator,
    delete_coordinator,
    get_coordinator_by_id,
    list_coordinators,
    set_coordinator_active,
)
from ..decorators import admin_required

logger = logging.getLogger(__name__)


def _coordinators_dashboard() -> str:
    """Render the coordinator management dashboard."""
    try:
        coordinators = list_coordinators()
    except Exception as e:  # pragma: no cover - defensive guard
        logger.error(f"Unable to list coordinators: {e}")
        flash("Unable to list coordinators.", "danger")
        coordinators: list[Any] = []

    total = len(coordinators)
    total_active = sum(1 for coord in coordinators if coord.is_active)

    return render_template(
        "admins/coordinators.html",
        coordinators=coordinators,
        total_coordinators=total,
        total_active_coordinators=total_active,
        inactive_coordinators=total - total_active,
    )


def _add_coordinator() -> ResponseReturnValue:
    """Create a new coordinator from the submitted username."""

    username = request.form.get("username", "").strip()
    if not username:
        flash("Username is required to add a coordinator.", "danger")
        return redirect(url_for("admin.coordinators.dashboard"))

    try:
        record = add_coordinator(username)
    except UserNotFoundError as exc:
        logger.error("UserNotFoundError: %s", exc)
        flash(f"User '{username}' does not exist", "warning")
    except DuplicateUserError:
        logger.error(f"Coordinator '{username}' already exists")
        flash(f"Coordinator '{username}' already exists", "warning")
    except (LookupError, ValueError):
        logger.exception("Unable to Add coordinator.")
        flash(f"Unable to add '{username}' as coordinator", "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to add coordinator.")
        flash("Unable to add coordinator.", "danger")
    else:
        flash(f"Coordinator '{record.username}' added.", "success")

    return redirect(url_for("admin.coordinators.dashboard"))


def _set_record_active_status(coordinator_id: int, is_active: bool) -> ResponseReturnValue:
    """Shared helper to update coordinator is_active status."""
    try:
        record = set_coordinator_active(coordinator_id, is_active)
        if record is None:
            raise LookupError(f"Coordinator with id {coordinator_id} not found")
    except LookupError:
        logger.exception("Unable to update coordinator.")
        flash("Unable to update coordinator", "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to update coordinator.")
        flash("Unable to update coordinator status. Please try again.", "danger")
    else:
        state = "activated" if record.is_active else "deactivated"
        flash(f"Coordinator '{record.username}' {state}.", "success")

    return redirect(url_for("admin.coordinators.dashboard"))


def _delete_coordinator(coordinator_id: int) -> ResponseReturnValue:
    """Remove a coordinator entirely."""

    try:
        record = get_coordinator_by_id(coordinator_id)
        if record is None:
            raise LookupError(f"Coordinator with id {coordinator_id} not found")
        delete_coordinator(coordinator_id)
    except LookupError:
        logger.exception("Unable to delete coordinator.")
        flash(f"Coordinator id {coordinator_id} was not found", "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to delete coordinator.")
        flash("Unable to delete coordinator. Please try again.", "danger")
    else:
        flash(f"Coordinator '{coordinator_id}' removed.", "success")

    return redirect(url_for("admin.coordinators.dashboard"))


class CoordinatorsRoutes:
    """Jobs management routes."""

    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        @admin_required
        def dashboard():
            return _coordinators_dashboard()

        @self.bp.post("/add")
        @admin_required
        def add() -> ResponseReturnValue:
            return _add_coordinator()

        @self.bp.post("/<int:coordinator_id>/activate")
        @admin_required
        def activate(coordinator_id: int) -> ResponseReturnValue:
            return _set_record_active_status(coordinator_id, True)

        @self.bp.post("/<int:coordinator_id>/deactivate")
        @admin_required
        def deactivate(coordinator_id: int) -> ResponseReturnValue:
            return _set_record_active_status(coordinator_id, False)

        @self.bp.post("/<int:coordinator_id>/delete")
        @admin_required
        def delete(coordinator_id: int) -> ResponseReturnValue:
            return _delete_coordinator(coordinator_id)


__all__ = [
    "CoordinatorsRoutes",
]
