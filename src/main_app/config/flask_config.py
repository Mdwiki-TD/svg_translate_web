import os

from .classes import DbConfig
from .main_settings import settings


def build_sqlalchemy_uri(db_config: DbConfig) -> str:
    """Build a SQLAlchemy database URI from a DbConfig dataclass.

    Used by Flask-SQLAlchemy configuration in create_app().
    Compatible with the existing build_db_url() in engine.py.
    """
    return f"mysql+pymysql://{db_config.db_user}:{db_config.db_password}@{db_config.db_host}/{db_config.db_name}"


class Config:
    """Base configuration class for Flask applications.

    This class provides Flask-standard configuration attributes that can be
    used with app.config.from_object(). It wraps the dataclass-based settings.
    """

    # Flask core settings
    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str | None = None
    SECRET_KEY_FALLBACKS: list[str] | None = None

    # Session cookie settings (populated from settings by default)
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    # CSRF protection settings
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: int | None = None  # None = tokens don't expire
    WTF_CSRF_SSL_STRICT: bool = True
    WTF_CSRF_CHECK_DEFAULT: bool = True  # default value
    WTF_CSRF_FIELD_NAME: str = "csrf_token"  # default value
    WTF_CSRF_HEADERS: list[str] = ["X-CSRFToken", "X-CSRF-Token"]  # default value
    WTF_CSRF_METHODS: list[str] = ["POST", "PUT", "PATCH", "DELETE"]  # default value
    # WTF_CSRF_SECRET_KEY: str = settings.security.secret_key # default value

    # Request handling
    MAX_CONTENT_LENGTH: int | None = 16 * 1024 * 1024  # 16MB default

    SQLALCHEMY_DATABASE_URI: str
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = None

    def __init__(self) -> None:
        """Initialize configuration with values from environment-based settings."""
        # Sync with the dataclass-based settings for backward compatibility
        self.SECRET_KEY = settings.security.secret_key
        self.SESSION_COOKIE_HTTPONLY = settings.cookie.httponly
        self.SESSION_COOKIE_SECURE = settings.cookie.secure
        self.SESSION_COOKIE_SAMESITE = settings.cookie.samesite

        # Load SECRET_KEY_FALLBACKS from environment for key rotation support
        # Format: comma-separated list of fallback keys
        # Example: FLASK_SECRET_KEY_FALLBACKS="old-key-1,old-key-2"
        fallbacks_str = os.getenv("FLASK_SECRET_KEY_FALLBACKS", "")
        if fallbacks_str:
            self.SECRET_KEY_FALLBACKS = [key.strip() for key in fallbacks_str.split(",") if key.strip()]

    def __post_init__(self):
        if self.SQLALCHEMY_ENGINE_OPTIONS is None:
            object.__setattr__(
                self,
                "SQLALCHEMY_ENGINE_OPTIONS",
                {
                    "pool_pre_ping": True,
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_recycle": 3600,
                    "connect_args": {
                        "connect_timeout": 5,
                        "init_command": 'SET time_zone = "+00:00"',
                        "charset": "utf8mb4",
                    },
                },
            )


class DevelopmentConfig(Config):
    """Development configuration with debugging enabled."""

    DEBUG: bool = True
    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_SSL_STRICT: bool = True

    # Production should always use secure cookies
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    # Configure CSRF token lifetime
    WTF_CSRF_TIME_LIMIT = settings.csrf_time_limit

    # Disable CORS for testing
    CORS_DISABLED: bool = True
    SQLALCHEMY_DATABASE_URI = build_sqlalchemy_uri(settings.database_data)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # Log SQL in development
    SQLALCHEMY_ENGINE_OPTIONS = {
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


class ProductionConfig(Config):
    """Production configuration with strict security settings."""

    DEBUG: bool = False
    TESTING: bool = False
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_SSL_STRICT: bool = True

    # Production should always use secure cookies
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"

    # Configure CSRF token lifetime
    WTF_CSRF_TIME_LIMIT = settings.csrf_time_limit

    CORS_DISABLED: bool = False
    SQLALCHEMY_DATABASE_URI = build_sqlalchemy_uri(settings.database_data)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
        "connect_args": {
            "connect_timeout": 5,
            "init_command": 'SET time_zone = "+00:00"',
            "charset": "utf8mb4",
        },
    }


class TestingConfig(Config):
    """Testing configuration with CSRF disabled for easier form testing."""

    # Prevent pytest from collecting this as a test class
    __test__ = False

    DEBUG: bool = False
    TESTING: bool = True
    WTF_CSRF_ENABLED: bool = False  # Disable CSRF for test requests
    SESSION_COOKIE_SECURE: bool = False

    # Use a fixed test secret key
    SECRET_KEY: str = "test-secret-key-not-for-production"

    # Disable CORS for testing
    CORS_DISABLED: bool = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
