"""Admin blueprint package."""

from dataclasses import dataclass, field
from typing import Any

from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from .coordinators import CoordinatorsRoutes
from .errors_route import CheckErrorsRoutes
from .jobs import AdminJobsRoutes
from .owid_charts import OwidChartsRoutes
from .settings import SettingsRoutes
from .slug_redirects import SlugRedirectsRoutes
from .templates import TemplatesRoutes
from .users import UsersRoutes


@dataclass(frozen=True)
class AdminRouteModule:
    route_cls: type
    name: str
    url_prefix: str = ""
    extra_kwargs: dict[str, Any] = field(default_factory=dict)


ADMIN_ROUTE_MODULES: list[AdminRouteModule] = [
    AdminRouteModule(route_cls=CoordinatorsRoutes, name="coordinators", url_prefix="/coordinators"),
    AdminRouteModule(route_cls=UsersRoutes, name="users", url_prefix="/users"),
    AdminRouteModule(route_cls=SettingsRoutes, name="settings", url_prefix="/settings"),
    AdminRouteModule(route_cls=TemplatesRoutes, name="templates", url_prefix="/templates"),
    AdminRouteModule(route_cls=OwidChartsRoutes, name="owidcharts", url_prefix="/owidcharts"),
    AdminRouteModule(route_cls=SlugRedirectsRoutes, name="slugredirects", url_prefix="/slugredirects"),
    AdminRouteModule(
        route_cls=AdminJobsRoutes,
        name="jobs",
        url_prefix="/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_admins,
            "bp_name": "adminpanel.jobs",
        },
    ),
    AdminRouteModule(route_cls=CheckErrorsRoutes, name="errors", url_prefix="/errors"),
]

__all__ = [
    "ADMIN_ROUTE_MODULES",
]
