#
from .admin.routes import bp_admin
from .api_routes import bp_api
from .auth.routes import bp_auth
from .main_routes.explorer_routes import bp_explorer
from .main_routes.extract_routes import bp_extract
from .main_routes.owid_charts_routes import bp_owid_charts
from .main_routes.routes import bp_main
from .public_jobs import bp_jobs

__all__ = [
    "bp_api",
    "bp_auth",
    "bp_jobs",
    "bp_main",
    "bp_explorer",
    "bp_admin",
    "bp_extract",
    "bp_owid_charts",
]
