"""Admin blueprint package."""

from flask import Blueprint

from .admin_panel import bp_admin
from .routes import (
    CoordinatorsRoutes,
    OwidChartsRoutes,
    SettingsRoutes,
    Templates,
    UsersRoutes,
    jobs_module,
    slug_redirects_module,
)


def register_bp_admin_blueprints(_bp: Blueprint) -> None:
    _bp.register_blueprint(CoordinatorsRoutes().bp)
    _bp.register_blueprint(UsersRoutes().bp)
    _bp.register_blueprint(SettingsRoutes().bp)
    _bp.register_blueprint(jobs_module.bp)
    _bp.register_blueprint(Templates().bp)
    _bp.register_blueprint(OwidChartsRoutes().bp)
    _bp.register_blueprint(slug_redirects_module.bp)


register_bp_admin_blueprints(bp_admin)
