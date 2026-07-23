""" """

from dataclasses import dataclass, field
from typing import Any

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .api_routes import ApiRoutes
from .auth.routes import AuthRoutes
from .jobs_utils_bp import UtilsJobsBp
from .main_routes import (
    ExplorerRoutes,
    ExtractRoutes,
    MainRoutes,
    OwidChartsRoutes,
)
from .profile import ProfileRoutes
from .public_jobs import PublicJobsRoutes


@dataclass(frozen=True)
class PublicRouteModule:
    route_cls: type
    name: str
    url_prefix: str
    extra_kwargs: dict[str, Any] = field(default_factory=dict)


PUBLIC_ROUTE_MODULES: list[PublicRouteModule] = [
    PublicRouteModule(MainRoutes, "main", "/main"),
    PublicRouteModule(AuthRoutes, "auth", ""),  # "/auth"
    PublicRouteModule(ProfileRoutes, "profile", "/profile"),
    PublicRouteModule(ExplorerRoutes, "explorer", "/explorer"),
    PublicRouteModule(ExtractRoutes, "extract", "/extract"),
    PublicRouteModule(ApiRoutes, "api", "/api"),
    PublicRouteModule(OwidChartsRoutes, "owid_charts", "/owidcharts"),
    PublicRouteModule(UtilsJobsBp, "jobs_utils", "/jobs_utils"),
    PublicRouteModule(
        PublicJobsRoutes,
        "public_jobs",
        "/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_public,
            "bp_name": "public_jobs",
        },
    ),
]


def register_blueprints(app: Flask) -> None:
    for module in PUBLIC_ROUTE_MODULES:
        bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
        route_instance = module.route_cls(bp=bp, **module.extra_kwargs)
        app.register_blueprint(route_instance.bp)


__all__ = [
    "register_blueprints",
]
