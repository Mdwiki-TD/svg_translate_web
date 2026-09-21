"""Admin blueprint package."""

from __future__ import annotations

from flask import Blueprint, Flask

from .admin_panel import AdminPanel
from .decorators import admin_guard
from .flask_admin_panel import add_admin_dashboard
from .routes import AdminRouteRegister


def register_bp_admin_blueprints(app: Flask) -> None:
    bp_admin = Blueprint("adminpanel", __name__, url_prefix="/adminpanel")
    # Reject every request to /adminpanel unless it comes from an active admin.
    # Flask propagates a parent blueprint's before_request to nested child
    # blueprints, so this single guard covers every admin sub-blueprint too.
    bp_admin.before_request(admin_guard)
    AdminPanel().register(bp_admin)
    AdminRouteRegister.register(bp_admin)
    app.register_blueprint(bp_admin)


__all__ = [
    "add_admin_dashboard",
    "register_bp_admin_blueprints",
]
