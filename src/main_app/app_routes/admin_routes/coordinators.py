""" """

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
from sqlalchemy.exc import IntegrityError

from ...db.services import admin_service
from ..admin.admins_required import admin_required

logger = logging.getLogger(__name__)

bp_coordinators = Blueprint("coordinators", __name__, url_prefix="/coordinators")


def _coordinators_dashboard() -> str:
    """Render the coordinator management dashboard."""

    coordinators = admin_service.list_coordinators()
    total = len(coordinators)
    active = sum(1 for coord in coordinators if coord.is_active)

    return render_template(
        "admins/coordinators.html",
        coordinators=coordinators,
        total_coordinators=total,
        active_coordinators=active,
        inactive_coordinators=total - active,
    )


def _add_coordinator() -> ResponseReturnValue:
    """Create a new coordinator from the submitted username."""

    username = request.form.get("username", "").strip()
    if not username:
        flash("Username is required to add a coordinator.", "danger")
        return redirect(url_for("admin.coordinators.dashboard"))

    try:
        record = admin_service.add_coordinator(username)
    except IntegrityError as exc:  # pragma: no cover - defensive guard
        if "a foreign key constraint fails" in str(exc):
            logger.error("IntegrityError: %s", exc)
            flash(f"Can't add coordinator. User: {username} does not exist.", "warning")
        else:
            logger.error("Unable to add coordinator.")
            flash("Unable to add coordinator.", "danger")
    except (LookupError, ValueError) as exc:
        logger.exception("Unable to Add coordinator.")
        flash(str(exc), "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to add coordinator.")
        flash("Unable to add coordinator.", "danger")
    else:
        flash(f"Coordinator '{record.username}' added.", "success")

    return redirect(url_for("admin.coordinators.dashboard"))


def _update_coordinator_active(coordinator_id: int) -> ResponseReturnValue:
    """Toggle the active flag for a coordinator."""

    desired = request.form.get("active", "0") == "1"
    try:
        record = admin_service.set_coordinator_active(coordinator_id, desired)
    except LookupError as exc:
        logger.exception("Unable to update coordinator.")
        flash(str(exc), "warning")
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
        record = admin_service.get_coordinator_by_id(coordinator_id)
        username = record.username
        admin_service.delete_coordinator(coordinator_id)
    except LookupError as exc:
        logger.exception("Unable to delete coordinator.")
        flash(str(exc), "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to delete coordinator.")
        flash("Unable to delete coordinator. Please try again.", "danger")
    else:
        flash(f"Coordinator '{username}' removed.", "success")

    return redirect(url_for("admin.coordinators.dashboard"))


class Coordinators:
    def __init__(self, bp_coordinators: Blueprint) -> None:
        @bp_coordinators.get("/")
        @admin_required
        def dashboard():
            return _coordinators_dashboard()

        @bp_coordinators.post("/add")
        @admin_required
        def add() -> ResponseReturnValue:
            return _add_coordinator()

        @bp_coordinators.post("/<int:coordinator_id>/active")
        @admin_required
        def update_active(coordinator_id: int) -> ResponseReturnValue:
            return _update_coordinator_active(coordinator_id)

        @bp_coordinators.post("/<int:coordinator_id>/delete")
        @admin_required
        def delete(coordinator_id: int) -> ResponseReturnValue:
            return _delete_coordinator(coordinator_id)


Coordinators(bp_coordinators)


__all__ = [
    "bp_coordinators",
]
