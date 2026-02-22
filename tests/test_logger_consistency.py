"""Test that all modified modules use 'svg_translate' logger name."""

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "module_path,module_name",
    [
        ("src.app", "app"),
        ("src.main_app.app_routes.admin.admin_routes.coordinators", "coordinators"),
        ("src.main_app.app_routes.admin.admin_routes.templates", "templates"),
        ("src.main_app.app_routes.auth.oauth", "oauth"),
        ("src.main_app.app_routes.auth.routes", "routes"),
        ("src.main_app.app_routes.cancel_restart.routes", "cancel_restart_routes"),
        ("src.main_app.app_routes.explorer.compare", "compare"),
        ("src.main_app.app_routes.explorer.routes", "explorer_routes"),
        ("src.main_app.app_routes.explorer.thumbnail_utils", "thumbnail_utils"),
        ("src.main_app.app_routes.explorer.utils", "explorer_utils"),
        ("src.main_app.app_routes.main.routes", "main_routes"),
        ("src.main_app.app_routes.tasks.args_utils", "args_utils"),
        ("src.main_app.app_routes.tasks.routes", "task_routes"),
        ("src.main_app.app_routes.templates.routes", "templates_routes"),
        ("src.main_app.db.db_class", "db_class"),
        ("src.main_app.db.db_CoordinatorsDB", "db_CoordinatorsDB"),
        ("src.main_app.db.db_CreateUpdate", "db_CreateUpdate"),
        ("src.main_app.db.db_StageStore", "db_StageStore"),
        ("src.main_app.db.db_TasksListDB", "db_TasksListDB"),
        ("src.main_app.db.db_Templates", "db_Templates"),
        ("src.main_app.db.svg_db", "svg_db"),
        ("src.main_app.db.task_store_pymysql", "task_store_pymysql"),
        ("src.main_app.routes_utils", "routes_utils"),
        ("src.main_app.tasks.downloads.download", "download"),
        ("src.main_app.tasks.fix_nested.fix_nested_tasks", "fix_nested_tasks"),
        ("src.main_app.tasks.injects.inject_tasks", "inject_tasks"),
        ("src.main_app.tasks.texts.start_bot", "start_bot"),
        ("src.main_app.tasks.uploads.up", "up"),
        ("src.main_app.tasks.uploads.upload_bot", "upload_bot"),
        ("src.main_app.template_service", "template_service"),
        ("src.main_app.threads.task_threads", "task_threads"),
        ("src.main_app.threads.web_run_task", "web_run_task"),
        ("src.main_app.admins.admin_service", "admin_service"),
        ("src.main_app.users.store", "user_store"),
        ("src.main_app.app_routes.templates.category", "category"),
        ("src.main_app.tasks.texts.text_bot", "text_bot"),
        ("src.log", "log"),
    ],
)
def test_module_logger_name(module_path, module_name):
    """Test that module uses 'svg_translate' as logger name."""
    import importlib

    module = importlib.import_module(module_path)

    # Check if module has a logger
    if hasattr(module, "logger"):
        assert (
            module.logger.name == "svg_translate"
        ), f"{module_path} logger should use 'svg_translate', got '{module.logger.name}'"
