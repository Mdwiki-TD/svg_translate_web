"""Admin blueprint package."""

from flask import Blueprint, Flask

from .admin_panel import bp_admin
from .routes import (
    AdminJobsRoutes,
    CoordinatorsRoutes,
    OwidChartsRoutes,
    SettingsRoutes,
    Templates,
    UsersRoutes,
    slug_redirects_module,
)

from ..jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins

def register_bp_admin_blueprints(_bp) -> None:
    _bp.register_blueprint(CoordinatorsRoutes().bp)
    _bp.register_blueprint(UsersRoutes().bp)
    _bp.register_blueprint(SettingsRoutes().bp)

    # Public API module
    jobs_module = AdminJobsRoutes(
        bp=Blueprint("jobs", __name__, url_prefix="/jobs"),
        jobs_data_infos=jobs_data_admins,
        bp_name="admin.jobs",
    )

    _bp.register_blueprint(jobs_module.bp)
    _bp.register_blueprint(Templates().bp)
    _bp.register_blueprint(OwidChartsRoutes().bp)
    _bp.register_blueprint(slug_redirects_module.bp)


__all__ = [
    "bp_admin",
    "register_bp_admin_blueprints",
]
