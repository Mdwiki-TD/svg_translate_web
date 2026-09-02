"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# --- Helper Functions ---


def _env_bool(name: str, default: bool = False) -> bool:
    """Convert environment variable to boolean."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, safe: bool = False) -> int:
    """Convert environment variable to integer."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:  # pragma: no cover - defensive guard
        if not safe:
            raise ValueError(f"Environment variable {name} must be an integer") from exc
        else:
            return default


def resolve_path(_path) -> Path:
    """Expand environment variables and user home directory in paths."""
    _path = os.path.expandvars(str(_path))
    _path = Path(_path).expanduser()
    return _path


# --- Data Classes for Configuration Sections ---


@dataclass(frozen=True)
class OtherConfig:
    """configs not in specific sections"""

    csrf_time_limit: int | None  # None means never expire
    user_agent: str
    wiki_domain: str
    static_server: str
    tool_title: str

    @classmethod
    def load(cls) -> OtherConfig:
        # CSRF token lifetime (in seconds). Default 3600 (1 hour).
        # Set to 0 or None to disable expiration (not recommended for production).
        csrf_time_limit = _env_int("WTF_CSRF_TIME_LIMIT", 3600)
        if not csrf_time_limit or csrf_time_limit <= 0:
            csrf_time_limit = 3600

        wiki_domain = os.getenv("WIKI_DOMAIN") or "commons.wikimedia.org"
        static_server = os.getenv("STATIC_SERVER") or "https://tools-static.wmflabs.org/cdnjs"

        user_agent = os.getenv(
            "USER_AGENT",
            "Copy SVG Translations/1.0 (https://copy-svg-langs.toolforge.org; tools.copy-svg-langs@toolforge.org)",
        )

        tool_title = os.getenv("TOOL_TITLE") or "Copy SVG Translations"

        _config = OtherConfig(
            csrf_time_limit=csrf_time_limit,
            user_agent=user_agent,
            wiki_domain=wiki_domain,
            static_server=static_server,
            tool_title=tool_title,
        )

        return _config


@dataclass(frozen=True)
class JobsConfig:
    """Configuration for jobs."""

    jobs_max_workers: int
    jobs_log_lines: int
    priority_per_item: int | None = None

    @classmethod
    def load(cls) -> JobsConfig:
        # Background job runner sizing.
        jobs_max_workers = max(1, _env_int("JOBS_MAX_WORKERS", 2))
        jobs_log_lines = max(10, _env_int("JOBS_LOG_LINES", 200))

        priority_per_item = _env_int("PRIORITY_PER_ITEM", 0, safe=True)
        if priority_per_item == 0:
            priority_per_item = None

        _config = JobsConfig(
            jobs_max_workers=jobs_max_workers,
            jobs_log_lines=jobs_log_lines,
            priority_per_item=priority_per_item,
        )

        return _config


@dataclass(frozen=True)
class DbConfig:
    db_name: str
    db_host: str
    db_user: str | None
    db_password: str | None

    def to_json(self) -> dict[str, Any]:
        return {
            "db_name": self.db_name,
            "db_host": self.db_host,
            "db_user": self.db_user,
            "db_password": self.db_password,
        }

    @classmethod
    def load(cls) -> DbConfig:
        """
        Construct a DbConfig populated from environment variables.

        Reads TOOL_TOOLSDB_DBNAME and TOOL_TOOLSDB_HOST (defaulting to empty string) and TOOL_TOOLSDB_USER and TOOL_TOOLSDB_PASSWORD (defaulting to None) and returns a DbConfig with those values.

        Returns:
            DbConfig: Configuration with fields:
                - db_name: from TOOL_TOOLSDB_DBNAME (default "").
                - db_host: from TOOL_TOOLSDB_HOST (default "").
                - db_user: from TOOL_TOOLSDB_USER (or None).
                - db_password: from TOOL_TOOLSDB_PASSWORD (or None).
        """
        return DbConfig(
            db_name=os.getenv("TOOL_TOOLSDB_DBNAME", ""),
            db_host=os.getenv("TOOL_TOOLSDB_HOST", ""),
            db_user=os.getenv("TOOL_TOOLSDB_USER", None),
            db_password=os.getenv("TOOL_TOOLSDB_PASSWORD", None),
        )


@dataclass(frozen=True)
class Paths:
    log_dir: str
    jobs_path: str

    main_files_path: str
    svg_data: str
    svg_data_thumb: str
    fix_nested_data: str
    crop_main_files_path: str

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_any(cls, data: dict[str, Any] | Paths) -> Paths:
        if isinstance(data, Paths):
            return data

        return cls(
            log_dir=data.get("log_dir", ""),
            jobs_path=data.get("jobs_path", ""),
            main_files_path=data.get("main_files_path", ""),
            svg_data=data.get("svg_data", ""),
            svg_data_thumb=data.get("svg_data_thumb", ""),
            fix_nested_data=data.get("fix_nested_data", ""),
            crop_main_files_path=data.get("crop_main_files_path", ""),
        )

    @classmethod
    def load(cls) -> Paths:
        """
        Compute the filesystem paths the application will use.

        The paths are rooted at the MAIN_DIR environment variable if set, otherwise at the user's ~/data directory.

        Returns:
            Paths: A dataclass
        """
        main_dir = os.getenv("MAIN_DIR", "~/data")
        main_dir = resolve_path(main_dir)
        crop_main_files_path = f"{main_dir}/crop_main_files"

        crop_main_files_original = f"{crop_main_files_path}/original"
        crop_main_files_cropped = f"{crop_main_files_path}/cropped"

        Path(crop_main_files_original).mkdir(parents=True, exist_ok=True)
        Path(crop_main_files_cropped).mkdir(parents=True, exist_ok=True)

        _dirs = {
            "svg_data": f"{main_dir}/svg_data",
            "svg_data_thumb": f"{main_dir}/svg_data_thumb",
            "log_dir": f"{main_dir}/logs",
            "fix_nested_data": f"{main_dir}/fix_nested_data",
            "jobs_path": f"{main_dir}/svg_jobs",
            "main_files_path": f"{main_dir}/main_files",
            "crop_main_files_path": crop_main_files_path,
        }
        return Paths.from_any(_dirs)


@dataclass(frozen=True)
class CookieConfig:
    name: str
    max_age: int
    secure: bool
    httponly: bool
    samesite: str

    @classmethod
    def load(cls) -> CookieConfig:
        session_cookie_secure = _env_bool("SESSION_COOKIE_SECURE", default=True)
        session_cookie_httponly = _env_bool("SESSION_COOKIE_HTTPONLY", default=True)
        session_cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

        cookie = CookieConfig(
            name=os.getenv("AUTH_COOKIE_NAME", "uid_enc_copy"),
            max_age=_env_int("AUTH_COOKIE_MAX_AGE", 30 * 24 * 3600),
            secure=session_cookie_secure,
            httponly=session_cookie_httponly,
            samesite=session_cookie_samesite,
        )

        return cookie


@dataclass(frozen=True)
class SessionConfig:
    """Keys used for storing data in Flask session."""

    state_key: str
    request_token_key: str
    request_secret_key: str

    @classmethod
    def load(cls) -> SessionConfig:
        return cls(
            state_key=os.getenv("STATE_SESSION_KEY", "oauth_state_nonce"),
            request_token_key=os.getenv("REQUEST_TOKEN_SESSION_KEY", "state"),
            request_secret_key=os.getenv("REQUEST_SECRET_SESSION_KEY", "oauth_request_secret"),
        )


@dataclass(frozen=True)
class OAuthConfig:
    """MediaWiki OAuth specific configuration."""

    mw_uri: str
    consumer_key: str
    consumer_secret: str
    encryption_key: str | None

    @classmethod
    def load(cls) -> OAuthConfig:
        """
        Loads OAuth settings and validates them if enabled.

        Raises:
            RuntimeError: If OAUTH_ENCRYPTION_KEY is missing.
        """
        mw_uri = os.getenv("OAUTH_MWURI", "")
        consumer_key = os.getenv("OAUTH_CONSUMER_KEY", "")
        consumer_secret = os.getenv("OAUTH_CONSUMER_SECRET", "")
        encryption_key = os.getenv("OAUTH_ENCRYPTION_KEY", "")

        # Validate mandatory fields for OAuth
        if not all([mw_uri, consumer_key, consumer_secret]):
            raise RuntimeError(
                "MediaWiki OAuth configuration is incomplete. Set OAUTH_MWURI, OAUTH_CONSUMER_KEY, and OAUTH_CONSUMER_SECRET."
            )

        if not encryption_key:
            raise RuntimeError("OAUTH_ENCRYPTION_KEY environment variable is required")

        return OAuthConfig(
            mw_uri=mw_uri,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            encryption_key=encryption_key,
        )


@dataclass(frozen=True)
class CorsConfig:
    allowed_domains: list[str]

    @classmethod
    def load(cls) -> CorsConfig:
        # Load CORS configuration
        cors_domains_str = os.getenv("CORS_ALLOWED_DOMAINS", "medwiki.toolforge.org,mdwikicx.toolforge.org")
        cors_domains = [d.strip() for d in cors_domains_str.split(",") if d.strip()]

        return CorsConfig(
            allowed_domains=cors_domains,
        )


@dataclass(frozen=True)
class SecurityConfig:
    """Security configuration for Flask 3.1+ features."""

    secret_key: str
    salt: str
    max_content_length: int  # Maximum request size in bytes
    max_form_memory_size: int  # Maximum form data in memory in bytes
    max_form_parts: int  # Maximum number of form fields
    secret_key_fallbacks: tuple[str, ...]  # Fallback secret keys for rotation

    @classmethod
    def load(cls) -> SecurityConfig:
        """
        Load security configuration (Flask 3.1+ features)
        """
        # MAX_CONTENT_LENGTH: Maximum request size (default 100MB)
        max_content_length = _env_int("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)

        # MAX_FORM_MEMORY_SIZE: Maximum form data in memory (default 16MB)
        max_form_memory_size = _env_int("MAX_FORM_MEMORY_SIZE", 16 * 1024 * 1024)

        # MAX_FORM_PARTS: Maximum number of form fields (default 1000)
        max_form_parts = _env_int("MAX_FORM_PARTS", 1000)

        # SECRET_KEY_FALLBACKS: Comma-separated list of fallback secret keys for rotation
        secret_key_fallbacks_str = os.getenv("SECRET_KEY_FALLBACKS", "")
        secret_key_fallbacks = tuple(key.strip() for key in secret_key_fallbacks_str.split(",") if key.strip())

        secret_key = os.getenv("FLASK_SECRET_KEY", "")
        secret_salt = os.getenv("SECRET_SALT", "svg-translate")

        security_config = SecurityConfig(
            salt=secret_salt,
            secret_key=secret_key,
            max_content_length=max_content_length,
            max_form_memory_size=max_form_memory_size,
            max_form_parts=max_form_parts,
            secret_key_fallbacks=secret_key_fallbacks,
        )

        if not security_config.secret_key:
            raise RuntimeError("FLASK_SECRET_KEY environment variable is required")

        return security_config


@dataclass(frozen=True)
class Settings:
    """Main settings container."""

    # Nested configurations
    database_data: DbConfig
    paths: Paths
    cookie: CookieConfig
    sessions: SessionConfig
    oauth: OAuthConfig
    security: SecurityConfig
    other: OtherConfig
    jobs: JobsConfig
    # cors: CorsConfig

    @classmethod
    def load(cls) -> Settings:
        """
        Initialize and return a cached Settings object.
        Main entry point for application configuration.

        Returns:
            Settings: The populated application settings.

        Raises:
            RuntimeError: If FLASK_SECRET_KEY is not set.
            RuntimeError: If OAUTH_ENCRYPTION_KEY is missing.
            RuntimeError: If the OAuth configuration (OAUTH_MWURI, OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET) is incomplete.
        """
        return Settings(
            database_data=DbConfig.load(),
            paths=Paths.load(),
            cookie=CookieConfig.load(),
            sessions=SessionConfig.load(),
            oauth=OAuthConfig.load(),
            security=SecurityConfig.load(),
            other=OtherConfig.load(),
            # cors=CorsConfig.load(),
            jobs=JobsConfig.load(),
        )


__all__ = [
    "DbConfig",
    "Paths",
    "CookieConfig",
    "SessionConfig",
    "OAuthConfig",
    "JobsConfig",
    "Settings",
    "OtherConfig",
    "SecurityConfig",
    "CorsConfig",
]
