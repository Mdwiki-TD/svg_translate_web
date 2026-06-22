""" """

from flask import Flask

from ..admin.route import bp_admin
from .api_routes import bp_api
from .auth.routes import bp_auth
from .jobs_utils_bp import jobs_utils_module
from .main_routes.explorer_routes import bp_explorer
from .main_routes.extract_routes import bp_extract
from .main_routes.owid_charts_routes import bp_owid_charts
from .main_routes.routes import bp_main
from .profile import bp_profile
from .public_jobs import jobs_public_module


def register_blueprints(app: Flask) -> None:

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_profile)

    app.register_blueprint(jobs_public_module.bp)
    app.register_blueprint(jobs_utils_module.bp)
    app.register_blueprint(bp_explorer)
    app.register_blueprint(bp_extract)
    app.register_blueprint(bp_owid_charts)
    app.register_blueprint(bp_api)


__all__ = [
    "register_blueprints",
]
