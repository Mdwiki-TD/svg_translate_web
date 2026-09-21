"""Admin blueprint package."""

from __future__ import annotations

from flask import Blueprint, Flask

from .admin_panel import AdminPanel
from .flask_admin_panel import add_admin_dashboard
from .routes import AdminRouteRegister


def register_bp_admin_blueprints(app: Flask) -> None:
    bp_admin = Blueprint("adminpanel", __name__, url_prefix="/adminpanel")
    AdminPanel().register(bp_admin)
    AdminRouteRegister.register(bp_admin)
    app.register_blueprint(bp_admin)


__all__ = [
    "add_admin_dashboard",
    "register_bp_admin_blueprints",
]
