#
from .admin.routes import bp_admin
from .auth.routes import bp_auth
from .copy_svg_langs_job.routes import bp_tasks
from .fix_nested import bp_fix_nested
from .main_routes.explorer_routes import bp_explorer
from .main_routes.extract_routes import bp_extract
from .main_routes.owid_charts_routes import bp_owid_charts
from .main_routes.routes import bp_main
from .main_routes.templates_routes import bp_templates

__all__ = [
    "bp_auth",
    "bp_main",
    "bp_explorer",
    "bp_templates",
    "bp_tasks",
    "bp_admin",
    "bp_fix_nested",
    "bp_extract",
    "bp_owid_charts",
]
