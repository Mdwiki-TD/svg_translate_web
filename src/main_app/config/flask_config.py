from sqlalchemy import URL

from .classes import DbConfig
from .main_settings import settings


def build_sqlalchemy_uri(db_config: DbConfig) -> str:
    """Build a SQLAlchemy database URI from a DbConfig dataclass.

    Used by Flask-SQLAlchemy configuration in create_app().
    Compatible with the existing build_db_url() in engine.py.
    """
    url = URL.create(
        "mysql+pymysql",
        username=db_config.db_user,
        password=db_config.db_password,
        host=db_config.db_host,
        database=db_config.db_name,
    ).render_as_string(hide_password=False)
    return url


def _resolve_db_uri() -> str:
    """Return MySQL URI when DB is configured, sqlite in-memory otherwise."""
    if settings.database_data.db_host or settings.database_data.db_user:
        return build_sqlalchemy_uri(settings.database_data)
    return "sqlite:///:memory:"


class Config:
    """Base configuration class for Flask applications.

    All attributes are class-level so ``app.config.from_object()`` can read them.
    Values are pulled from the environment-based ``settings`` singleton at
    module import time.
    """

    # Flask core settings
    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str = settings.security.secret_key
    SECRET_KEY_FALLBACKS: list[str] = list(settings.security.secret_key_fallbacks or [])

    # Session cookie settings
    SESSION_COOKIE_HTTPONLY: bool = settings.cookie.httponly
    SESSION_COOKIE_SECURE: bool = settings.cookie.secure
    SESSION_COOKIE_SAMESITE: str = settings.cookie.samesite

    # CSRF protection settings
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int | None = settings.csrf_time_limit
    WTF_CSRF_SSL_STRICT: bool = True
    WTF_CSRF_CHECK_DEFAULT: bool = True
    WTF_CSRF_FIELD_NAME: str = "csrf_token"
    WTF_CSRF_HEADERS: list[str] = ["X-CSRFToken", "X-CSRF-Token"]
    WTF_CSRF_METHODS: list[str] = ["POST", "PUT", "PATCH", "DELETE"]

    # Flask 3.1+ security configurations
    MAX_CONTENT_LENGTH: int | None = settings.security.max_content_length
    MAX_FORM_MEMORY_SIZE: int = settings.security.max_form_memory_size
    MAX_FORM_PARTS: int = settings.security.max_form_parts

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI: str = _resolve_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 3600,
        "connect_args": {
            "connect_timeout": 5,
            "init_command": 'SET time_zone = "+00:00"',
            "charset": "utf8mb4",
        },
    }


class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""

    DEBUG: bool = True
    TESTING: bool = True
    SQLALCHEMY_ECHO: bool = True  # Log SQL in development

    # Disable CORS for testing
    CORS_DISABLED: bool = True


class ProductionConfig(Config):
    """Production configuration with strict security settings."""

    CORS_DISABLED: bool = False


class TestingConfig(Config):
    """Testing configuration with CSRF disabled for easier form testing."""

    __test__ = False  # prevent pytest collection

    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = False  # Disable CSRF for test requests
    SESSION_COOKIE_SECURE: bool = False

    # Use a fixed test secret key
    SECRET_KEY: str = "test-secret-key-not-for-production"

    # Disable CORS for testing
    CORS_DISABLED: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS: dict = {}
    SQLALCHEMY_ECHO: bool = False
