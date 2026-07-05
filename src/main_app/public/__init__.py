""" """

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .api_routes import ApiRoutes
from .auth.routes import AuthRoutes
from .jobs_utils_bp import UtilsJobsBp
from .main_routes.explorer_routes import ExplorerRoutes
from .main_routes.extract_routes import ExtractRoutes
from .main_routes.owid_charts_routes import OwidChartsRoutes
from .main_routes.routes import MainRoutes
from .profile import ProfileRoutes
from .public_jobs import PublicJobsRoutes


def register_blueprints(app: Flask) -> None:
    bp_main = Blueprint("main", __name__)
    main_model = MainRoutes(bp_main)

    # Public API module
    jobs_public_module = PublicJobsRoutes(
        bp=Blueprint("public_jobs", __name__, url_prefix="/jobs"),
        jobs_data_infos=jobs_data_public,
        bp_name="public_jobs",
    )

    bp_owid_charts = Blueprint("owid_charts", __name__, url_prefix="/owidcharts")
    owid_charts_model = OwidChartsRoutes(bp_owid_charts)

    # Public API module
    jobs_utils_module = UtilsJobsBp(
        Blueprint("jobs_utils", __name__, url_prefix="/jobs_utils")
    )

    bp_auth = Blueprint("auth", __name__)
    auth_model = AuthRoutes(bp_auth)

    bp_profile = Blueprint("profile", __name__, url_prefix="/profile")
    profile_model = ProfileRoutes(bp_profile)

    bp_explorer = Blueprint("explorer", __name__, url_prefix="/explorer")
    explorer_model = ExplorerRoutes(bp_explorer)

    bp_extract = Blueprint("extract", __name__, url_prefix="/extract")
    extract_model = ExtractRoutes(bp_extract)

    bp_api = Blueprint("api", __name__, url_prefix="/api")
    api_model = ApiRoutes(bp_api)

    app.register_blueprint(auth_model.bp)
    app.register_blueprint(profile_model.bp)
    app.register_blueprint(explorer_model.bp)
    app.register_blueprint(extract_model.bp)
    app.register_blueprint(api_model.bp)

    app.register_blueprint(main_model.bp)
    app.register_blueprint(jobs_public_module.bp)
    app.register_blueprint(jobs_utils_module.bp)
    app.register_blueprint(owid_charts_model.bp)


__all__ = [
    "register_blueprints",
]
