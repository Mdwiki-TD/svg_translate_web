"""Admin blueprint package."""

from dataclasses import dataclass, field
from typing import Any

from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from .coordinators import CoordinatorsRoutes
from .jobs import AdminJobsRoutes
from .owid_charts import OwidChartsRoutes
from .settings import SettingsRoutes
from .slug_redirects import SlugRedirects
from .templates import Templates
from .users import UsersRoutes


@dataclass(frozen=True)
class AdminRouteModule:
    route_cls: type
    name: str
    url_prefix: str = ""
    extra_kwargs: dict[str, Any] = field(default_factory=dict)


ADMIN_ROUTE_MODULES: list[AdminRouteModule] = [
    AdminRouteModule(CoordinatorsRoutes, "coordinators", "/coordinators"),
    AdminRouteModule(UsersRoutes, "users", "/users"),
    AdminRouteModule(SettingsRoutes, "settings", "/settings"),
    AdminRouteModule(Templates, "templates", "/templates"),
    AdminRouteModule(OwidChartsRoutes, "owidcharts", "/owidcharts"),
    AdminRouteModule(SlugRedirects, "slugredirects", "/slugredirects"),
    AdminRouteModule(
        AdminJobsRoutes,
        "jobs",
        "/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_admins,
            "bp_name": "adminpanel.jobs",
        },
    ),
]

__all__ = [
    "ADMIN_ROUTE_MODULES",
]
