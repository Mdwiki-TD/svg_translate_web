"""
Flask application factory.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, render_template, request

from .admin import AdminsRouteRegister
from .config import Config, ConfigLoader, get_settings
from .database import init_db
from .database.exceptions import DatabaseInitError
from .error_pages import register_cache_headers, register_error_pages
from .extensions import csrf_init_app
from .extensions import db as _db
from .extensions import migrate
from .jobs_workers.cli_jobs import register_cli_jobs
from .logger_config import LoggingConfigurator
from .public import PublicRouteRegister
from .public.routes_utils import context_data
from .services.core import CookieHeaderClient, filters, init_rate_limiter

logger = logging.getLogger(__name__)


class AppFactory:
    """Builds and configures the Flask application."""

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

        cls._init_logging(app)
        cls._register_template_context(app)
        cls._init_extensions(app)

        db_is_ok = True
        # Initialize Flask-SQLAlchemy and Flask-Migrate
        if app.config.get("SQLALCHEMY_DATABASE_URI"):
            db_is_ok = cls.init_app_and_db(app, _db)

        init_rate_limiter(app)
        if db_is_ok:
            cls._register_routes(app)
        else:
            app.before_request(cls.db_error_fallback)
        return app

    @staticmethod
    def _init_logging(app: Flask):
        level = logging.DEBUG if app.config["DEBUG"] else logging.INFO
        use_color = app.config["IS_PRODUCTION"] is False
        daily_rotation = app.config["IS_PRODUCTION"] is True

        LoggingConfigurator.configure_logging(
            level=level,
            name="main_app",
            use_colorlog=use_color,
            daily_rotation=daily_rotation,
        )

    @staticmethod
    def _init_extensions(app: Flask):
        # Initialize CSRF protection
        csrf_init_app(app)

        app.jinja_env.filters.update(filters)

        app_settings = get_settings()
        app_settings.ensure_directories()
        register_error_pages(app)
        register_cache_headers(app)

    @staticmethod
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

    @staticmethod
    def _register_routes(app: Flask) -> None:
        PublicRouteRegister.register(app)
        AdminsRouteRegister.register(app, _db)
        register_cli_jobs(app)

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

        return context_data(
            app_settings.other.wiki_domain,
            app_settings.other.static_server,
            tool_title=app_settings.other.tool_title,
        )


__all__ = [
    "AppFactory",
]
