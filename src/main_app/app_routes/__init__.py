#
from .admin.routes import bp_admin
from .auth.routes import bp_auth
from .explorer.routes import bp_explorer
from .extract import bp_extract
from .fix_nested import bp_fix_nested, bp_fix_nested_explorer
from .main.routes import bp_main
from .owid_charts_routes import bp_owid_charts
from .templates.routes import bp_templates

from .tasks.routes import bp_tasks

__all__ = [
    "bp_auth",
    "bp_main",
    "bp_explorer",
    "bp_templates",
    "bp_tasks",
    "bp_admin",
    "bp_fix_nested",
    "bp_fix_nested_explorer",
    "bp_extract",
    "bp_owid_charts",
]
