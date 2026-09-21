"""
Coordinators Management Views.
"""

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

from ...database.exceptions import DuplicateRecordError, UserNotFoundError
from ...database.services import AdminService
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class CoordinatorDashboardView(MethodView):
    """View to handle listing and rendering the coordinator management dashboard."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.admin_service = AdminService()

    def get(self) -> str:
        """Render the coordinator management dashboard."""
        try:
            coordinators = self.admin_service.list_coordinators()
        except Exception as e:  # pragma: no cover - defensive guard
            logger.error("Unable to list coordinators: %s", e)
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


class AddCoordinatorView(MethodView):
    """View to handle adding a new coordinator."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.admin_service = AdminService()

    def post(self) -> ResponseReturnValue:
        """Create a new coordinator from the submitted username."""
        username = request.form.get("username", "").strip()
        if not username:
            flash("Username is required to add a coordinator.", "danger")
            return redirect(url_for("adminpanel.coordinators.dashboard"))

        try:
            record = self.admin_service.add_coordinator(username)
        except UserNotFoundError as exc:
            logger.error("UserNotFoundError: %s", exc)
            flash(f"User '{username}' does not exist", "warning")
        except DuplicateRecordError:
            logger.error("Coordinator '%s' already exists", username)
            flash(f"Coordinator '{username}' already exists", "warning")
        except (LookupError, ValueError):
            logger.exception("Unable to Add coordinator.")
            flash(f"Unable to add '{username}' as coordinator", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to add coordinator.")
            flash("Unable to add coordinator.", "danger")
        else:
            flash(f"Coordinator '{record.username}' added.", "success")

        return redirect(url_for("adminpanel.coordinators.dashboard"))


class CoordinatorStatusView(MethodView):
    """Base class for managing coordinator status updates."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.admin_service = AdminService()

    def _set_record_active_status(self, coordinator_id: int, is_active: bool) -> ResponseReturnValue:
        """Shared helper to update coordinator is_active status."""
        try:
            record = self.admin_service.set_coordinator_active(coordinator_id, is_active)
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

        return redirect(url_for("adminpanel.coordinators.dashboard"))


class ActivateCoordinatorView(CoordinatorStatusView):
    """View to activate a coordinator."""

    def post(self, coordinator_id: int) -> ResponseReturnValue:
        return self._set_record_active_status(coordinator_id, True)


class DeactivateCoordinatorView(CoordinatorStatusView):
    """View to deactivate a coordinator."""

    def post(self, coordinator_id: int) -> ResponseReturnValue:
        return self._set_record_active_status(coordinator_id, False)


class DeleteCoordinatorView(MethodView):
    """View to remove a coordinator entirely."""

    decorators = [admin_required]

    def __init__(self) -> None:
        self.admin_service = AdminService()

    def post(self, coordinator_id: int) -> ResponseReturnValue:
        """Remove a coordinator entirely."""
        try:
            record = self.admin_service.get_coordinator_by_id(coordinator_id)
            if record is None:
                raise LookupError(f"Coordinator with id {coordinator_id} not found")
            self.admin_service.delete(coordinator_id)
        except LookupError:
            logger.exception("Unable to delete coordinator.")
            flash(f"Coordinator id {coordinator_id} was not found", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to delete coordinator.")
            flash("Unable to delete coordinator. Please try again.", "danger")
        else:
            flash(f"Coordinator '{coordinator_id}' removed.", "success")

        return redirect(url_for("adminpanel.coordinators.dashboard"))


class CoordinatorView:
    """Coordinator management routes registrar using Class-Based Views."""

    def register(self, bp: Blueprint) -> None:
        # Register views on the Blueprint using as_view
        bp.add_url_rule(
            "/",
            view_func=CoordinatorDashboardView.as_view("dashboard"),
        )
        bp.add_url_rule(
            "/add",
            view_func=AddCoordinatorView.as_view("add"),
        )
        bp.add_url_rule(
            "/<int:coordinator_id>/activate",
            view_func=ActivateCoordinatorView.as_view("activate"),
        )
        bp.add_url_rule(
            "/<int:coordinator_id>/deactivate",
            view_func=DeactivateCoordinatorView.as_view("deactivate"),
        )
        bp.add_url_rule(
            "/<int:coordinator_id>/delete",
            view_func=DeleteCoordinatorView.as_view("delete"),
        )


__all__ = [
    "CoordinatorView",
]
