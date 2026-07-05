""" """

from flask import Blueprint, Flask

from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .api_routes import bp_api
from .auth.routes import bp_auth
from .jobs_utils_bp import UtilsJobsBp
from .main_routes.explorer_routes import bp_explorer
from .main_routes.extract_routes import bp_extract
from .main_routes.owid_charts_routes import bp_owid_charts
from .main_routes.routes import bp_main
from .profile import bp_profile
from .public_jobs import PublicJobsRoutes


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_profile)

    # Public API module
    jobs_public_module = PublicJobsRoutes(
        bp=Blueprint("public_jobs", __name__, url_prefix="/jobs"),
        jobs_data_infos=jobs_data_public,
        bp_name="public_jobs",
    )

    # Public API module
    jobs_utils_module = UtilsJobsBp(
        Blueprint("jobs_utils", __name__, url_prefix="/jobs_utils")
    )

    app.register_blueprint(jobs_public_module.bp)
    app.register_blueprint(jobs_utils_module.bp)
    app.register_blueprint(bp_explorer)
    app.register_blueprint(bp_extract)
    app.register_blueprint(bp_owid_charts)
    app.register_blueprint(bp_api)


__all__ = [
    "register_blueprints",
]
