"""Flask application factory."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Tuple

from flask import Flask, flash, render_template
from flask_wtf.csrf import CSRFProtect

from .app_routes import (
    bp_admin,
    bp_auth,
    bp_explorer,
    bp_extract,
    bp_fix_nested,
    bp_fix_nested_explorer,
    bp_main,
    bp_tasks,
    bp_tasks_managers,
    bp_templates,
    close_task_store,
)
from .config import settings
from .cookies import CookieHeaderClient
from .db import close_cached_db
from .users.current import context_user
from .users.store import ensure_user_token_table

logger = logging.getLogger("svg_translate")


def format_stage_timestamp(value: str) -> str:
    """Format ISO8601 like '2025-10-27T04:41:07' to 'Oct 27, 2025, 4:41 AM'."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
    except Exception:
        logger.exception("Failed to parse timestamp: %s", value)
        return ""
    # convert 24h → 12h with AM/PM
    hour24 = dt.hour
    ampm = "AM" if hour24 < 12 else "PM"
    hour12 = hour24 % 12 or 12
    minute = f"{dt.minute:02d}"
    month = dt.strftime("%b")  # Oct
    return f"{month} {dt.day}, {dt.year}, {hour12}:{minute} {ampm}"


def create_app() -> Flask:
    """Instantiate and configure the Flask application."""

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.url_map.strict_slashes = False
    app.test_client_class = CookieHeaderClient
    app.secret_key = settings.secret_key
    app.config.update(
        SESSION_COOKIE_HTTPONLY=settings.cookie.httponly,
        SESSION_COOKIE_SECURE=settings.cookie.secure,
        SESSION_COOKIE_SAMESITE=settings.cookie.samesite,
    )

    app.config["USE_MW_OAUTH"] = settings.use_mw_oauth

    # Initialize CSRF protection
    csrf = CSRFProtect(app)  # noqa: F841

    if settings.use_mw_oauth and (settings.db_data.get("host") or settings.db_data.get("db_connect_file")):
        ensure_user_token_table()

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_tasks)
    app.register_blueprint(bp_explorer)
    app.register_blueprint(bp_templates)
    app.register_blueprint(bp_tasks_managers)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_fix_nested)
    app.register_blueprint(bp_fix_nested_explorer)
    app.register_blueprint(bp_extract)

    @app.context_processor
    def _inject_user():  # pragma: no cover - trivial wrapper
        return context_user()

    app.jinja_env.globals.setdefault("USE_MW_OAUTH", settings.use_mw_oauth)
    app.jinja_env.filters["format_stage_timestamp"] = format_stage_timestamp

    @app.teardown_appcontext
    def _cleanup_connections(exception: Exception | None) -> None:  # pragma: no cover - teardown
        close_cached_db()
        close_task_store()

    @app.errorhandler(404)
    def page_not_found(e: Exception) -> Tuple[str, int]:
        """Handle 404 errors"""
        logger.error("Page not found: %s", e)
        flash("Page not found", "warning")
        return render_template("index.html", title="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_server_error(e: Exception) -> Tuple[str, int]:
        """Handle 500 errors"""
        logger.error("Internal Server Error: %s", e)
        flash("Internal Server Error", "danger")
        return render_template("index.html", title="Internal Server Error"), 500

    return app
