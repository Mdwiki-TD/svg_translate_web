#
from .admin.routes import bp_admin
from .auth.routes import bp_auth
from .cancel_restart.routes import bp_tasks_managers
from .explorer.routes import bp_explorer
from .extract import bp_extract
from .fix_nested import bp_fix_nested, bp_fix_nested_explorer
from .main.routes import bp_main
from .tasks.routes import bp_tasks, close_task_store
from .templates.routes import bp_templates

__all__ = [
    "bp_auth",
    "bp_main",
    "bp_explorer",
    "bp_templates",
    "bp_tasks",
    "bp_tasks_managers",
    "bp_admin",
    "bp_fix_nested",
    "bp_fix_nested_explorer",
    "bp_extract",
    "close_task_store",
]
