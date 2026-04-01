"""Flask application factory."""

from __future__ import annotations

import logging
from typing import Tuple

from flask import Flask, flash, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from .app_routes import (
    bp_admin,
    bp_auth,
    bp_explorer,
    bp_extract,
    bp_fix_nested,
    bp_main,
    bp_owid_charts,
    bp_tasks,
    bp_templates,
)
from .config import settings
from .core.cookies import CookieHeaderClient
from .db import close_cached_db
from .db.user_tokens import ensure_user_token_table
from .services.copy_svg_langs_service import close_task_store
from .services.users_service import context_user
from .utils import format_stage_timestamp, short_url

logger = logging.getLogger(__name__)


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(bp_main)
    app.register_blueprint(bp_tasks)
    app.register_blueprint(bp_explorer)
    app.register_blueprint(bp_templates)
    app.register_blueprint(bp_admin)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_fix_nested)
    app.register_blueprint(bp_extract)
    app.register_blueprint(bp_owid_charts)


def register_error_pages(app: Flask):
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


def update_app_config(app: Flask) -> None:
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

    update_app_config(app)

    # Configure CSRF token lifetime
    app.config["WTF_CSRF_TIME_LIMIT"] = settings.csrf_time_limit

    # Initialize CSRF protection
    csrf = CSRFProtect(app)  # noqa: F841

    if settings.database_data.db_host or settings.database_data.db_user:
        ensure_user_token_table()

    @app.context_processor
    def _inject_user():  # pragma: no cover - trivial wrapper
        return context_user()

    app.jinja_env.filters["format_stage_timestamp"] = format_stage_timestamp
    app.jinja_env.filters["short_url"] = short_url

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

    register_error_pages(app)
    register_blueprints(app)

    return app
