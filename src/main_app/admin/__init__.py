"""Admin blueprint package."""

from flask import Blueprint, Flask

from ..jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from .admin_panel import AdminPanel
from .flask_admin_panel import add_admin_dashboard
from .routes import (
    AdminJobsRoutes,
    CoordinatorsRoutes,
    OwidChartsRoutes,
    SettingsRoutes,
    SlugRedirects,
    Templates,
    UsersRoutes,
)


def register_bp_admin_blueprints(app: Flask) -> None:
    bp_admin = Blueprint("adminpanel", __name__, url_prefix="/adminpanel")
    admin_model = AdminPanel(bp_admin)  # noqa: F841

    bp_coords = Blueprint("coordinators", __name__, url_prefix="/coordinators")
    coords_model = CoordinatorsRoutes(bp_coords)

    bp_users = Blueprint("users", __name__, url_prefix="/users")
    users_model = UsersRoutes(bp_users)

    # Settings module
    bp_settings = Blueprint("settings", __name__, url_prefix="/settings")
    settings_module = SettingsRoutes(bp_settings)

    # Public API module
    jobs_module = AdminJobsRoutes(
        bp=Blueprint("jobs", __name__, url_prefix="/jobs"),
        jobs_data_infos=jobs_data_admins,
        bp_name="adminpanel.jobs",
    )

    bp_templates = Blueprint("templates", __name__, url_prefix="/templates")
    templates_model = Templates(bp_templates)

    bp_owidcharts = Blueprint("owidcharts", __name__, url_prefix="/owidcharts")
    owid_model = OwidChartsRoutes(bp_owidcharts)

    bp_slug_redirects = Blueprint("slugredirects", __name__, url_prefix="/slugredirects")
    slug_redirects_model = SlugRedirects(bp_slug_redirects)

    # Register blueprints
    bp_admin.register_blueprint(coords_model.bp)
    bp_admin.register_blueprint(users_model.bp)
    bp_admin.register_blueprint(settings_module.bp)
    bp_admin.register_blueprint(jobs_module.bp)

    bp_admin.register_blueprint(templates_model.bp)
    bp_admin.register_blueprint(owid_model.bp)
    bp_admin.register_blueprint(slug_redirects_model.bp)

    app.register_blueprint(bp_admin)


__all__ = [
    "add_admin_dashboard",
    "register_bp_admin_blueprints",
]
