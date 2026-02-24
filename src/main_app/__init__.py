"""Flask application factory."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Tuple

from flask import Flask, flash, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

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

logger = logging.getLogger(__name__)

print(__name__)


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
    """
    Create and configure and return the Flask application used by the project.

    The returned app is configured with custom template and static folders, session cookie
    settings from project settings, CSRF protection, registered
    application blueprints, a user context processor, a Jinja filter for stage timestamps,
    teardown handlers that close cached connections and task store, and handlers for 404
    and 500 errors.

    Returns:
        Flask: The fully configured Flask application instance.
    """

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
        # Flask 3.1+ security configurations
        MAX_CONTENT_LENGTH=settings.security.max_content_length,
        MAX_FORM_MEMORY_SIZE=settings.security.max_form_memory_size,
        MAX_FORM_PARTS=settings.security.max_form_parts,
        SECRET_KEY_FALLBACKS=list(settings.security.secret_key_fallbacks),
    )

    # Configure CSRF token lifetime
    app.config["WTF_CSRF_TIME_LIMIT"] = settings.csrf_time_limit

    # Initialize CSRF protection
    csrf = CSRFProtect(app)  # noqa: F841

    if settings.database_data.db_host or settings.database_data.db_user:
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

    app.jinja_env.filters["format_stage_timestamp"] = format_stage_timestamp

    @app.teardown_appcontext
    def _cleanup_connections(exception: Exception | None) -> None:  # pragma: no cover - teardown
        # Idempotent teardown - safe for Flask 3.1.2+ stream_with_context regression
        # See: https://github.com/pallets/flask/issues/5804
        try:
            close_cached_db()
        except Exception:
            logger.debug("Failed to close cached DB during teardown", exc_info=True)
        try:
            close_task_store()
        except Exception:
            logger.debug("Failed to close task store during teardown", exc_info=True)

    @app.errorhandler(400)
    def bad_request(e: Exception) -> Tuple[str, int]:
        """Handle 400 errors"""
        logger.error("Bad request: %s", e)
        flash("Invalid request", "warning")
        return render_template("index.html", title="Bad Request"), 400

    @app.errorhandler(403)
    def forbidden(e: Exception) -> Tuple[str, int]:
        """Handle 403 errors"""
        logger.error("Forbidden access: %s", e)
        flash("Access denied", "danger")
        return render_template("index.html", title="Access Denied"), 403

    @app.errorhandler(404)
    def page_not_found(e: Exception) -> Tuple[str, int]:
        """Handle 404 errors"""
        logger.error("Page not found: %s", e)
        flash("Page not found", "warning")
        return render_template("index.html", title="Page Not Found"), 404

    @app.errorhandler(405)
    def method_not_allowed(e: Exception) -> Tuple[str, int]:
        """Handle 405 errors"""
        logger.error("Method not allowed: %s", e)
        flash("Method not allowed", "warning")
        return render_template("index.html", title="Method Not Allowed"), 405

    @app.errorhandler(500)
    def internal_server_error(e: Exception) -> Tuple[str, int]:
        """Handle 500 errors"""
        logger.error("Internal Server Error: %s", e)
        flash("Internal Server Error", "danger")
        return render_template("index.html", title="Internal Server Error"), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError) -> Tuple[str, int]:
        """Handle CSRF token errors"""
        logger.error("CSRF error: %s", e)
        flash("Session expired or invalid. Please try again.", "warning")
        return render_template("index.html", title="Session Expired"), 400

    return app
