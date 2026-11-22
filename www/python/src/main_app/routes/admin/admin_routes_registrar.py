"""Admin blueprint package."""

from __future__ import annotations

from typing import Any

from flask import Blueprint, Flask
from flask_sqlalchemy import SQLAlchemy

from ...decorators.admin_decorators import admin_guard
from .admin_panel import AdminPanel
from .admin_sidebar import create_admin_sidebar
from .flask_admin_panel import add_admin_dashboard

from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from ..public.shared_jobs_registrar import SharedJobRoutesRegistrar
from ..models import RouteModule
from .routes.admins import AdminView
from .routes.error_logs import CheckErrorLogsView
from .routes.errors_route import CheckErrorsView
from .routes.owid_charts import OwidChartsRoutes
from .routes.settings import SettingsRoutes
from .routes.slug_redirects import SlugRedirectsRoutes
from .routes.templates import TemplatesRoutes
from .routes.toolforge_jobs_view import ToolforgeJobsView
from .routes.users import UsersRoutes

ADMIN_ROUTE_MODULES: list[RouteModule] = [
    RouteModule(route_cls=AdminView, name="admins", url_prefix="/admins"),
    RouteModule(route_cls=UsersRoutes, name="users", url_prefix="/users"),
    RouteModule(route_cls=SettingsRoutes, name="settings", url_prefix="/settings"),
    RouteModule(route_cls=TemplatesRoutes, name="templates", url_prefix="/templates"),
    RouteModule(route_cls=OwidChartsRoutes, name="owidcharts", url_prefix="/owidcharts"),
    RouteModule(route_cls=SlugRedirectsRoutes, name="slugredirects", url_prefix="/slugredirects"),
    RouteModule(
        route_cls=SharedJobRoutesRegistrar,
        name="jobs",
        url_prefix="/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_admins,
            "bp_name": "admin_panel.jobs",
        },
    ),
    RouteModule(route_cls=CheckErrorsView, name="errors", url_prefix="/errors"),
    RouteModule(route_cls=CheckErrorLogsView, name="error_logs", url_prefix="/error-logs"),
    RouteModule(route_cls=ToolforgeJobsView, name="tfj", url_prefix="/tfj"),
]


class AdminSubRoutesRegister:
    @staticmethod
    def register(bp_admin: Blueprint) -> None:
        for module in ADMIN_ROUTE_MODULES:
            bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
            instance = module.route_cls()
            instance.register(bp, **module.extra_kwargs)
            bp_admin.register_blueprint(bp)


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

    @classmethod
    def register(cls, app: Flask, _db: SQLAlchemy) -> None:
        bp = Blueprint(
            "admin_panel",
            __name__,
            url_prefix="/admin_panel",
        )

        cls.register_guard(bp)

        bp.app_context_processor(cls.inject_sidebar)

        AdminPanel.register(bp)
        AdminSubRoutesRegister.register(bp)
        add_admin_dashboard(app, _db)
        app.register_blueprint(bp)


__all__ = [
    "AdminsRouteRegister",
]
