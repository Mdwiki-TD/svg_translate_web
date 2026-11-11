"""Admin/Coordinator blueprint package."""

from __future__ import annotations

from flask import Blueprint

from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from ...models import RouteModule
from ...public.shared_jobs_registrar import SharedJobRoutesRegistrar
from .admins import AdminView
from .error_logs import CheckErrorLogsView
from .errors_route import CheckErrorsView
from .owid_charts import OwidChartsRoutes
from .settings import SettingsRoutes
from .slug_redirects import SlugRedirectsRoutes
from .templates import TemplatesRoutes
from .users import UsersRoutes

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
]


class AdminSubRoutesRegister:
    @staticmethod
    def register(bp_admin: Blueprint) -> None:
        for module in ADMIN_ROUTE_MODULES:
            bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
            instance = module.route_cls()
            instance.register(bp, **module.extra_kwargs)
            bp_admin.register_blueprint(bp)


__all__ = [
    "AdminSubRoutesRegister",
]
