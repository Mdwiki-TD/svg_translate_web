"""
Application configuration.
"""

from __future__ import annotations

import os
from typing import Any

from .classes import get_settings


class Config:
    """Base configuration class for Flask applications.

    All attributes are class-level so ``app.config.from_object()`` can read them.
    Values are pulled from the environment-based ``settings`` singleton at
    module import time.
    """

    app_settings = get_settings()
    # Flask core settings
    DEBUG: bool = False
    TESTING: bool = False
    IS_PRODUCTION: bool = False
    SECRET_KEY: str = app_settings.security.secret_key
    SECRET_KEY_FALLBACKS: list[str] = list(app_settings.security.secret_key_fallbacks or [])

    # Session cookie settings
    SESSION_COOKIE_HTTPONLY: bool = app_settings.cookie.httponly
    SESSION_COOKIE_SECURE: bool = app_settings.cookie.secure
    SESSION_COOKIE_SAMESITE: str = app_settings.cookie.samesite

    # CSRF protection settings
    WTF_CSRF_ENABLED: bool = True
    # CSRF token lifetime (in seconds). Default 3600 (1 hour).
    # None = tokens don't expire
    WTF_CSRF_TIME_LIMIT: int | None = app_settings.other.csrf_time_limit

    WTF_CSRF_SSL_STRICT: bool = True
    WTF_CSRF_CHECK_DEFAULT: bool = True
    WTF_CSRF_FIELD_NAME: str = "csrf_token"
    WTF_CSRF_HEADERS: list[str] = ["X-CSRFToken", "X-CSRF-Token"]
    WTF_CSRF_METHODS: list[str] = ["POST", "PUT", "PATCH", "DELETE"]
    # WTF_CSRF_SECRET_KEY: str = settings.security.secret_key

    # Flask 3.1+ security configurations

    # Maximum form data in memory (default 16MB)
    MAX_CONTENT_LENGTH: int | None = app_settings.security.max_content_length

    # Maximum form data in memory in bytes (default 16MB)
    MAX_FORM_MEMORY_SIZE: int = app_settings.security.max_form_memory_size

    # Maximum number of form fields (default 1000)
    MAX_FORM_PARTS: int = app_settings.security.max_form_parts

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("DATABASE_URI", "")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict[str, Any] = {}

    SQLALCHEMY_ECHO: bool = False
    RATELIMIT_STORAGE_URI = "memory://"

    def __init__(self) -> None:
        app_settings = get_settings()
        """Initialize configuration with values from environment-based settings."""
        # Sync with the dataclass-based settings for backward compatibility
        self.SECRET_KEY = app_settings.security.secret_key
        self.SESSION_COOKIE_HTTPONLY = app_settings.cookie.httponly
        self.SESSION_COOKIE_SECURE = app_settings.cookie.secure
        self.SESSION_COOKIE_SAMESITE = app_settings.cookie.samesite

        # Only set MySQL-specific engine options if URI is MySQL (not SQLite)
        uri = self.SQLALCHEMY_DATABASE_URI or ""
        if uri.startswith("mysql") and not self.SQLALCHEMY_ENGINE_OPTIONS:
            self.SQLALCHEMY_ENGINE_OPTIONS = {
                "pool_pre_ping": True,
                "pool_size": 5,
                "max_overflow": 10,
                "pool_recycle": 3600,
                "connect_args": {
                    "connect_timeout": 5,
                    "init_command": 'SET time_zone = "+00:00"',
                    "charset": "utf8mb4",
                    "collation": "utf8mb4_unicode_ci",
                },
            }


class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""

    DEBUG: bool = True
    TESTING: bool = True
    SQLALCHEMY_ECHO: bool = False  # Log SQL in development

    # Production should always use secure cookies
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    # Disable CORS for testing
    CORS_DISABLED: bool = True


class ProductionConfig(Config):
    """Production configuration with strict security settings."""

    # Production should always use secure cookies
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    CORS_DISABLED: bool = False
    IS_PRODUCTION: bool = True
    RATELIMIT_STORAGE_URI = "memory://"


class TestingConfig(Config):
    """Testing configuration with CSRF disabled for easier form testing."""

    __test__ = False  # prevent pytest collection

    DEBUG: bool = False
    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = False  # Disable CSRF for test requests
    SESSION_COOKIE_SECURE: bool = False

    # Use a fixed test secret key
    SECRET_KEY: str = "test-secret-key-not-for-production"

    # Disable CORS for testing
    CORS_DISABLED: bool = True

    # Use SQLite in-memory for tests (no MySQL dependency)
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"  # pyright: ignore[reportIncompatibleVariableOverride]
    SQLALCHEMY_ENGINE_OPTIONS: dict[str, Any] = {}  # SQLite doesn't need MySQL options


class ConfigLoader:
    """Resolves the correct config class from FLASK_ENV."""

    _CONFIG_MAP: dict[str, type[Config]] = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }

    @classmethod
    def load(cls) -> type[Config]:
        env = os.environ.get("FLASK_ENV", "production")
        return cls._CONFIG_MAP.get(env, ProductionConfig)


__all__ = [
    "Config",
    "DevelopmentConfig",
    "ProductionConfig",
    "TestingConfig",
    "ConfigLoader",
]
