"""
Flask application factory.
"""

from __future__ import annotations

import logging
from typing import Any, Tuple, Type

from flask import Flask, flash, render_template
from flask_wtf.csrf import CSRFError, CSRFProtect

from .app_routes import register_blueprints
from .app_routes.utils import context_user
from .config import ensure_directories, settings
from .core.cookies import CookieHeaderClient
from .core.jinja_filters import filters
from .db import init_db
from .db.exceptions import DatabaseInitError
from .extensions import db as _db
from .extensions import migrate
from .jobs_workers.cli_jobs import register_cli_jobs

logger = logging.getLogger(__name__)


def register_error_pages(app: Flask) -> None:
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


def init_app_and_db(app, _db) -> bool:
    _db.init_app(app)
    migrate.init_app(app, _db)

    try:
        with app.app_context():
            # Create database tables and views if they don't exist
            init_db(_db)
        return True
    except DatabaseInitError as exc:
        logger.error("%s", exc)
    except Exception as e:
        logger.error("Failed to create tables: %s", e)

    return False


def create_app(config_class: Type) -> Flask:
    """Instantiate and configure the Flask application.

    Args:
        config_class: Configuration class for ``app.config.from_object()``.
            When *None*, auto-detected from the ``FLASK_ENV`` environment
            variable (defaults to ``ProductionConfig``).

    Returns:
        Configured Flask application instance.
    """

    if config_class is None:
        raise ValueError("config_class must be provided")

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.url_map.strict_slashes = False
    app.test_client_class = CookieHeaderClient
    app.config.from_object(config_class())

    # Initialize CSRF protection
    csrf = CSRFProtect(app)  # noqa: F841

    @app.context_processor
    def _inject_user() -> dict[str, Any]:
        return context_user(settings.other.wiki_domain, settings.other.static_server)

    app.jinja_env.filters.update(filters)

    @app.teardown_appcontext
    def _cleanup_connections(exception: Exception | None) -> None:  # pragma: no cover - teardown
        # Idempotent teardown - safe for Flask 3.1.2+ stream_with_context regression
        # See: https://github.com/pallets/flask/issues/5804
        # try:
        #     close_cached_db()
        # except Exception:
        #     logger.debug("Failed to close cached DB during teardown", exc_info=True)
        pass

    db_is_ok = True
    # Initialize Flask-SQLAlchemy and Flask-Migrate
    if app.config.get("SQLALCHEMY_DATABASE_URI"):
        db_is_ok = init_app_and_db(app, _db)

    ensure_directories()
    register_error_pages(app)

    if db_is_ok:
        register_blueprints(app)
        register_cli_jobs(app)
    else:

        @app.before_request
        def db_error_fallback():
            from flask import request

            if request.endpoint == "static":
                return None
            return render_template("index_db_error.html"), 503

    return app


__all__ = [
    "register_error_pages",
    "init_app_and_db",
    "create_app",
]
