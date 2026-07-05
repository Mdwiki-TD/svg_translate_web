""" """

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .api_routes import bp_api
from .auth.routes import bp_auth
from .jobs_utils_bp import UtilsJobsBp
from .main_routes.explorer_routes import bp_explorer
from .main_routes.extract_routes import bp_extract
from .main_routes.owid_charts_routes import OwidChartsRoutes
from .main_routes.routes import MainRoutes
from .profile import bp_profile
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

    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_profile)
    app.register_blueprint(bp_explorer)
    app.register_blueprint(bp_extract)
    app.register_blueprint(bp_api)

    app.register_blueprint(main_model.bp)
    app.register_blueprint(jobs_public_module.bp)
    app.register_blueprint(jobs_utils_module.bp)
    app.register_blueprint(owid_charts_model.bp)


__all__ = [
    "register_blueprints",
]
