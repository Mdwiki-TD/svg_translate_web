"""Admin blueprint package."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Flask

from ..decorators.admin_decorators import admin_guard
from .admin_panel import AdminPanel
from .admin_sidebar import create_admin_sidebar
from .flask_admin_panel import add_admin_dashboard
from .routes import AdminSubRoutesRegister


class AdminsRouteRegister:
    """Registers all route blueprints on a Flask app."""

    @staticmethod
    def inject_sidebar() -> dict[str, Any]:
        """Provide the admin sidebar markup as a template global."""
        return {
            "create_admin_sidebar": create_admin_sidebar,
        }

    @staticmethod
    def register_guard(bp: Blueprint) -> None:
        # Reject every request to /admin_panel unless it comes from an active admin.
        # Flask propagates a parent blueprint's before_request to nested child
        # blueprints, so this single guard covers every admin sub-blueprint too.
        bp.before_request(admin_guard)


def register_bp_admin_blueprints(app: Flask) -> None:
    bp = Blueprint("adminpanel", __name__, url_prefix="/adminpanel")
    AdminPanel.register(bp)
    AdminSubRoutesRegister.register(bp)
    app.register_blueprint(bp)


__all__ = [
    "add_admin_dashboard",
    "register_bp_admin_blueprints",
]
