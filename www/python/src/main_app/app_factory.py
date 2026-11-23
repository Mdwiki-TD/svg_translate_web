"""
Flask application factory.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

from .cli import CliFactory
from .config import Config, ConfigLoader, get_settings
from .database import DatabaseBuilder
from .database import db as _db
from .extensions import csrf_init_app, migrate
from .routes import RoutesFactory
from .routes.error_pages import register_error_handlers
from .routes.public.routes_utils import RequestContextHelper
from .services.core import CookieHeaderClient, filters, init_rate_limiter

logger = logging.getLogger(__name__)


class AppFactory:
    """Builds and configures the Flask application."""

    @staticmethod
    def init_app_and_db(app, db: SQLAlchemy) -> bool:
        db.init_app(app)
        return DatabaseBuilder.build(db, app)

    @classmethod
    def create(cls, config_class: type[Config] | None = None) -> Flask:
        config_class = config_class or ConfigLoader.load()

        app = Flask(
            __name__,
            template_folder="../templates",
            static_folder="../static",
        )

        app.url_map.strict_slashes = False
        app.test_client_class = CookieHeaderClient
        app.config.from_object(config_class())

        cls._register_template_context(app)
        cls._init_extensions(app)

        db_is_ok = True
        # Initialize Flask-SQLAlchemy and Flask-Migrate
        if app.config.get("SQLALCHEMY_DATABASE_URI"):
            migrate.init_app(app, _db)
            db_is_ok = cls.init_app_and_db(app, _db)

        init_rate_limiter(app)
        if db_is_ok:
            RoutesFactory.register(app, _db)
        else:
            app.before_request(cls.db_error_fallback)
        return app

    @staticmethod
    def _init_extensions(app: Flask):
        # Initialize CSRF protection
        csrf_init_app(app)
        register_error_handlers(app)
        CliFactory.register(app)

        app.jinja_env.filters.update(filters)
        get_settings().ensure_directories()

    @staticmethod
    def db_error_fallback():
        if request.endpoint == "static":
            return None
        return render_template("index_db_error.html"), 503

    @classmethod
    def _register_template_context(cls, app: Flask):
        """Inject global variables into all templates."""

        app.context_processor(cls.inject_globals)

    @staticmethod
    def inject_globals() -> dict[str, Any]:  # pragma: no cover - trivial wrapper
        app_settings = get_settings()

        return RequestContextHelper.context_data(
            app_settings.other.wiki_domain,
            app_settings.other.static_server,
            tool_title=app_settings.other.tool_title,
        )


__all__ = [
    "AppFactory",
]
