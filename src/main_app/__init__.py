"""
Flask application factory.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, Response, flash, jsonify, render_template, request
from flask_wtf.csrf import CSRFError

from .admin import add_admin_dashboard, register_bp_admin_blueprints
from .config import ensure_directories, settings
from .database import init_db
from .database.exceptions import DatabaseInitError
from .error_pages import register_error_pages
from .extensions import (
    csrf_init_app,
)
from .extensions import db as _db
from .extensions import (
    migrate,
)
from .jobs_workers.cli_jobs import register_cli_jobs
from .public import register_blueprints
from .public.utils import context_data
from .shared.core import CookieHeaderClient, filters

logger = logging.getLogger(__name__)


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


def create_app(config_class: type) -> Flask:
    """Instantiate and configure the Flask application.

    Args:
        config_class: configuration class to use.

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
    csrf_init_app(app)

    @app.context_processor
    def inject_globals() -> dict[str, Any]:  # pragma: no cover - trivial wrapper
        return context_data(
            settings.other.wiki_domain,
            settings.other.static_server,
            tool_title="Copy SVG Translations",
        )

    app.jinja_env.filters.update(filters)

    db_is_ok = True
    # Initialize Flask-SQLAlchemy and Flask-Migrate
    if app.config.get("SQLALCHEMY_DATABASE_URI"):
        db_is_ok = init_app_and_db(app, _db)

    ensure_directories()
    register_error_pages(app)

    if db_is_ok:
        add_admin_dashboard(app, _db)
        register_bp_admin_blueprints(app)
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
    "create_app",
]
