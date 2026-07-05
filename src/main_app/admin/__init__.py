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
    SlugRedirects,
)

from ..jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins

def register_bp_admin_blueprints(app: Flask) -> None:
    bp_admin.register_blueprint(CoordinatorsRoutes().bp)
    bp_admin.register_blueprint(UsersRoutes().bp)
    bp_admin.register_blueprint(SettingsRoutes().bp)
    bp_admin.register_blueprint(Templates().bp)
    bp_admin.register_blueprint(OwidChartsRoutes().bp)
    bp_admin.register_blueprint(SlugRedirects().bp)

    # Public API module
    jobs_module = AdminJobsRoutes(
        bp=Blueprint("jobs", __name__, url_prefix="/jobs"),
        jobs_data_infos=jobs_data_admins,
        bp_name="admin.jobs",
    )

    bp_admin.register_blueprint(jobs_module.bp)

    app.register_blueprint(bp_admin)

__all__ = [
    "register_bp_admin_blueprints",
]
