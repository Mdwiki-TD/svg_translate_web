""" """

from flask import Blueprint, Flask

from ..models import RouteModule

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .api_routes import ApiRoutes
from .auth.routes import AuthView
from .jobs_utils_bp import UtilsJobsBpRoutes
from .main_routes import (
    ExplorerView,
    ExtractView,
    InjectView,
    MainView,
    OwidChartsRoutes,
    TemplatesView,
    TranslateView,
)
from .profile import ProfileView
from .public_jobs import PublicJobsRoutes


PUBLIC_ROUTE_MODULES: list[RouteModule] = [
    RouteModule(route_cls=MainView, name="main", url_prefix=""),
    RouteModule(route_cls=AuthView, name="auth", url_prefix=""),  # "/auth"
    RouteModule(route_cls=ProfileView, name="profile", url_prefix="/profile"),
    RouteModule(route_cls=ExplorerView, name="explorer", url_prefix="/explorer"),
    RouteModule(route_cls=ExtractView, name="extract", url_prefix="/extract"),
    RouteModule(route_cls=InjectView, name="inject", url_prefix="/inject"),
    RouteModule(route_cls=TranslateView, name="translate", url_prefix="/translate"),
    RouteModule(route_cls=ApiRoutes, name="api", url_prefix="/api"),
    RouteModule(route_cls=OwidChartsRoutes, name="owid_charts", url_prefix="/owidcharts"),
    RouteModule(route_cls=UtilsJobsBpRoutes, name="jobs_utils", url_prefix="/jobs_utils"),
    RouteModule(route_cls=TemplatesView, name="templates", url_prefix="/templates"),
    RouteModule(
        route_cls=PublicJobsRoutes,
        name="public_jobs",
        url_prefix="/jobs",
        extra_kwargs={
            "jobs_data_infos": jobs_data_public,
            "bp_name": "public_jobs",
        },
    ),
]


class PublicRouteRegister:
    """Registers all route blueprints on a Flask app."""

    @staticmethod
    def register(app: Flask) -> None:
        for module in PUBLIC_ROUTE_MODULES:
            bp = Blueprint(module.name, __name__, url_prefix=module.url_prefix)
            instance = module.route_cls(**module.extra_kwargs)
            instance.register(bp)
            app.register_blueprint(bp)


__all__ = [
    "PublicRouteRegister",
]
