"""
Admins Management Views.
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
from ...decorators import admin_required

logger = logging.getLogger(__name__)


class BaseView(MethodView):
    def __init__(self) -> None:
        self.service = AdminService()


class AdminDashboardView(BaseView):
    """View to handle listing and rendering the admin management dashboard."""

    decorators = [admin_required]

    def get(self) -> str:
        """Render the admin management dashboard."""
        try:
            admins = self.service.list_admins()
        except Exception as e:  # pragma: no cover - defensive guard
            logger.error("Unable to list admins: %s", e)
            flash("Unable to list admins.", "danger")
            admins: list[Any] = []

        total = len(admins)
        total_active = sum(1 for coord in admins if coord.is_active)

        return render_template(
            "admins/admins.html",
            admins=admins,
            total_admins=total,
            total_active_admins=total_active,
            inactive_admins=total - total_active,
        )


class AddAdminView(BaseView):
    """View to handle adding a new admin."""

    decorators = [admin_required]

    def post(self) -> ResponseReturnValue:
        """Create a new admin from the submitted username."""
        username = request.form.get("username", "").strip()
        if not username:
            flash("Username is required to add an admin.", "danger")
            return redirect(url_for("admin_panel.admins.dashboard"))

        try:
            record = self.service.add_admin(username)
        except UserNotFoundError as exc:
            logger.error("UserNotFoundError: %s", exc)
            flash(f"User '{username}' does not exist", "warning")
        except DuplicateRecordError:
            logger.error("Admin '%s' already exists", username)
            flash(f"Admin '{username}' already exists", "warning")
        except (LookupError, ValueError):
            logger.exception("Unable to Add admin.")
            flash(f"Unable to add '{username}' as admin", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to add admin.")
            flash("Unable to add admin.", "danger")
        else:
            flash(f"Admin '{record.username}' added.", "success")

        return redirect(url_for("admin_panel.admins.dashboard"))


class AdminStatusView(BaseView):
    """Base class for managing admin status updates."""

    decorators = [admin_required]

    def _set_record_active_status(
        self,
        admin_id: int,
        is_active: bool,
    ) -> ResponseReturnValue:
        """Shared helper to update admin is_active status."""
        try:
            record = self.service.set_admin_active(admin_id, is_active)
            if record is None:
                raise LookupError(f"Admin with id {admin_id} not found")
        except LookupError:
            logger.exception("Unable to update admin.")
            flash("Unable to update admin", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to update admin.")
            flash("Unable to update admin status. Please try again.", "danger")
        else:
            state = "activated" if record.is_active else "deactivated"
            flash(f"Admin '{record.username}' {state}.", "success")

        return redirect(url_for("admin_panel.admins.dashboard"))


class ActivateAdminView(AdminStatusView):
    """View to activate an admin."""

    def post(self, admin_id: int) -> ResponseReturnValue:
        return self._set_record_active_status(admin_id, True)


class DeactivateAdminView(AdminStatusView):
    """View to deactivate an admin."""

    def post(self, admin_id: int) -> ResponseReturnValue:
        return self._set_record_active_status(admin_id, False)


class DeleteAdminView(BaseView):
    """View to remove an admin entirely."""

    decorators = [admin_required]

    def post(self, admin_id: int) -> ResponseReturnValue:
        """Remove an admin entirely."""
        try:
            record = self.service.get_admin_by_id(admin_id)
            if record is None:
                raise LookupError(f"Admin with id {admin_id} not found")
            self.service.delete(admin_id)
        except LookupError:
            logger.exception("Unable to delete admin.")
            flash(f"Admin id {admin_id} was not found", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to delete admin.")
            flash("Unable to delete admin. Please try again.", "danger")
        else:
            flash(f"Admin '{admin_id}' removed.", "success")

        return redirect(url_for("admin_panel.admins.dashboard"))


class AdminView:
    """Admin management routes registrar using Class-Based Views."""

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        # Register views on the Blueprint using as_view
        bp.add_url_rule(
            "/",
            view_func=AdminDashboardView.as_view("dashboard"),
        )
        bp.add_url_rule(
            "/add",
            view_func=AddAdminView.as_view("add"),
        )
        bp.add_url_rule(
            "/<int:admin_id>/activate",
            view_func=ActivateAdminView.as_view("activate"),
        )
        bp.add_url_rule(
            "/<int:admin_id>/deactivate",
            view_func=DeactivateAdminView.as_view("deactivate"),
        )
        bp.add_url_rule(
            "/<int:admin_id>/delete",
            view_func=DeleteAdminView.as_view("delete"),
        )


__all__ = [
    "AdminView",
]
