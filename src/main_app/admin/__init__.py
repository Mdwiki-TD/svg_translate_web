"""Admin blueprint package."""

from flask import Blueprint, Flask

from .admin_panel import AdminPanel
from .routes import ADMIN_ROUTE_MODULES


def register_admin_blueprints(bp_admin: Blueprint) -> None:
    for module in ADMIN_ROUTE_MODULES:
        bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
        route_instance = module.route_cls(bp=bp, **module.extra_kwargs)
        bp_admin.register_blueprint(route_instance.bp)


def register_bp_admin_blueprints(app: Flask) -> None:
    bp_admin = Blueprint("adminpanel", __name__, url_prefix="/adminpanel")
    admin_model = AdminPanel(bp_admin)

    register_admin_blueprints(admin_model.bp)
    app.register_blueprint(admin_model.bp)


__all__ = [
    "register_bp_admin_blueprints",
]
