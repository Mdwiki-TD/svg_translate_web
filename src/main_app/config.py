"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DbConfig:
    db_name: str
    db_host: str
    db_user: str | None
    db_password: str | None


@dataclass(frozen=True)
class Paths:
    svg_data: str
    svg_data_thumb: str
    log_dir: str
    fix_nested_data: str
    svg_jobs_path: str
    main_files_path: str
    crop_main_files_path: str


@dataclass(frozen=True)
class CookieConfig:
    name: str
    max_age: int
    secure: bool
    httponly: bool
    samesite: str


@dataclass(frozen=True)
class OAuthConfig:
    mw_uri: str
    consumer_key: str
    consumer_secret: str
    user_agent: str
    upload_host: str


@dataclass(frozen=True)
class DownloadConfig:
    """Configuration for download jobs."""

    dev_limit: int  # Limit for downloads in development mode (0 = unlimited)


@dataclass(frozen=True)
class SecurityConfig:
    """Security configuration for Flask 3.1+ features."""

    max_content_length: int  # Maximum request size in bytes
    max_form_memory_size: int  # Maximum form data in memory in bytes
    max_form_parts: int  # Maximum number of form fields
    secret_key_fallbacks: tuple[str, ...]  # Fallback secret keys for rotation


class DynamicSettingsStore:
    """Lazy loader and cacher for settings stored in the database."""

    def __init__(self, db_config: DbConfig):
        self._db_config = db_config
        self._cache: Dict[str, Any] | None = None

    def get_all(self) -> Dict[str, Any]:
        """Get all dynamic settings, loading from db if not cached."""
        if self._cache is not None:
            return dict(self._cache)

        # Lazy import to avoid circular dependencies
        from .db.db_Settings import SettingsDB
        db = SettingsDB(self._db_config)
        self._cache = db.get_all()
        return dict(self._cache)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific dynamic setting by key."""
        return self.get_all().get(key, default)

    def invalidate(self) -> None:
        """Clear the cache to force reload on next access."""
        self._cache = None


@dataclass(frozen=True)
class Settings:
    is_localhost: callable
    database_data: DbConfig
    STATE_SESSION_KEY: str
    REQUEST_TOKEN_SESSION_KEY: str
    secret_key: str
    oauth_encryption_key: str
    cookie: CookieConfig
    oauth: OAuthConfig
    paths: Paths
    disable_uploads: str
    download: DownloadConfig
    security: SecurityConfig
    csrf_time_limit: Optional[int]  # None means never expire
    dynamic: DynamicSettingsStore


def _load_db_data_new() -> DbConfig:
    """
    Construct a DbConfig populated from environment variables.

    Reads DB_NAME and DB_HOST (defaulting to empty string) and TOOL_REPLICA_USER and TOOL_REPLICA_PASSWORD (defaulting to None) and returns a DbConfig with those values.

    Returns:
        DbConfig: Configuration with fields:
            - db_name: from DB_NAME (default "").
            - db_host: from DB_HOST (default "").
            - db_user: from TOOL_REPLICA_USER (or None).
            - db_password: from TOOL_REPLICA_PASSWORD (or None).
    """
    return DbConfig(
        db_name=os.getenv("DB_NAME", ""),
        db_host=os.getenv("DB_HOST", ""),
        db_user=os.getenv("TOOL_REPLICA_USER", None),
        db_password=os.getenv("TOOL_REPLICA_PASSWORD", None),
    )


def _get_paths() -> Paths:
    """
    Compute the filesystem paths the application uses for SVG data, thumbnails, logs, fix data, and SVG job files and ensure those directories exist.

    The paths are rooted at the MAIN_DIR environment variable if set, otherwise at the user's ~/data directory.

    Returns:
        Paths: A dataclass with the following populated fields:
            - svg_data: path for original SVG files
            - svg_data_thumb: path for SVG thumbnails
            - log_dir: path for log files
            - fix_nested_data: path for nested-fix data
            - svg_jobs_path: path for SVG job files
            - main_files_path: path for main files
    """
    main_dir = os.getenv("MAIN_DIR", os.path.join(os.path.expanduser("~"), "data"))
    svg_data = f"{main_dir}/svg_data"
    svg_data_thumb = f"{main_dir}/svg_data_thumb"
    log_dir = f"{main_dir}/logs"
    fix_nested_data = f"{main_dir}/fix_nested_data"
    svg_jobs_path = f"{main_dir}/svg_jobs"
    main_files_path = f"{main_dir}/main_files"
    crop_main_files_path = f"{main_dir}/crop_main_files"
    crop_main_files_original = f"{crop_main_files_path}/original"
    crop_main_files_cropped = f"{crop_main_files_path}/cropped"

    # Ensure directories exist
    Path(svg_data).mkdir(parents=True, exist_ok=True)
    Path(svg_data_thumb).mkdir(parents=True, exist_ok=True)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    Path(fix_nested_data).mkdir(parents=True, exist_ok=True)
    Path(svg_jobs_path).mkdir(parents=True, exist_ok=True)
    Path(main_files_path).mkdir(parents=True, exist_ok=True)
    Path(crop_main_files_original).mkdir(parents=True, exist_ok=True)
    Path(crop_main_files_cropped).mkdir(parents=True, exist_ok=True)

    return Paths(
        svg_data=svg_data,
        svg_data_thumb=svg_data_thumb,
        log_dir=log_dir,
        fix_nested_data=fix_nested_data,
        svg_jobs_path=svg_jobs_path,
        main_files_path=main_files_path,
        crop_main_files_path=crop_main_files_path,
    )


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Environment variable {name} must be an integer") from exc


def _load_oauth_config() -> Optional[OAuthConfig]:
    mw_uri = os.getenv("OAUTH_MWURI")
    consumer_key = os.getenv("OAUTH_CONSUMER_KEY")
    consumer_secret = os.getenv("OAUTH_CONSUMER_SECRET")
    if not (mw_uri and consumer_key and consumer_secret):
        return None

    return OAuthConfig(
        mw_uri=mw_uri,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        user_agent=os.getenv(
            "USER_AGENT",
            "Copy SVG Translations/1.0 (https://copy-svg-langs.toolforge.org; tools.copy-svg-langs@toolforge.org)",
        ),
        upload_host=os.getenv("UPLOAD_END_POINT", "commons.wikimedia.org"),
    )


def is_localhost(host: str) -> bool:
    local_hosts = [
        "localhost",
        "127.0.0.1",
    ]

    return any(x in host for x in local_hosts)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Assemble and return the application's Settings populated from environment variables.

    Reads and validates required environment variables, builds cookie, OAuth, path, and database configurations, and returns a consolidated Settings instance.

    Returns:
        Settings: The populated application settings.

    Raises:
        RuntimeError: If FLASK_SECRET_KEY is not set.
        RuntimeError: If OAUTH_ENCRYPTION_KEY is missing.
        RuntimeError: If the OAuth configuration (OAUTH_MWURI, OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET) is incomplete.
    """
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("FLASK_SECRET_KEY environment variable is required")

    session_cookie_secure = _env_bool("SESSION_COOKIE_SECURE", default=True)
    session_cookie_httponly = _env_bool("SESSION_COOKIE_HTTPONLY", default=True)
    session_cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    STATE_SESSION_KEY = os.getenv("STATE_SESSION_KEY", "oauth_state_nonce")
    REQUEST_TOKEN_SESSION_KEY = os.getenv("REQUEST_TOKEN_SESSION_KEY", "state")

    oauth_config = _load_oauth_config()

    oauth_encryption_key = os.getenv("OAUTH_ENCRYPTION_KEY")
    if not oauth_encryption_key:
        raise RuntimeError("OAUTH_ENCRYPTION_KEY environment variable is required")

    cookie = CookieConfig(
        name=os.getenv("AUTH_COOKIE_NAME", "uid_enc"),
        max_age=_env_int("AUTH_COOKIE_MAX_AGE", 30 * 24 * 3600),
        secure=session_cookie_secure,
        httponly=session_cookie_httponly,
        samesite=session_cookie_samesite,
    )

    # CSRF token lifetime (in seconds). Default 3600 (1 hour).
    # Set to 0 or None to disable expiration (not recommended for production).
    csrf_time_limit = _env_int("WTF_CSRF_TIME_LIMIT", 3600)
    if not csrf_time_limit or csrf_time_limit <= 0:
        csrf_time_limit = 3600

    if oauth_config is None:
        raise RuntimeError(
            "MediaWiki OAuth configuration is incomplete. Set OAUTH_MWURI, OAUTH_CONSUMER_KEY, and OAUTH_CONSUMER_SECRET."
        )

    # Load download configuration
    # DEV_DOWNLOAD_LIMIT: Limit number of downloads in development mode (0 = unlimited)
    dev_download_limit = _env_int("DEV_DOWNLOAD_LIMIT", 0)

    # Load security configuration (Flask 3.1+ features)
    # MAX_CONTENT_LENGTH: Maximum request size (default 100MB for SVG uploads)
    max_content_length = _env_int("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)
    # MAX_FORM_MEMORY_SIZE: Maximum form data in memory (default 16MB)
    max_form_memory_size = _env_int("MAX_FORM_MEMORY_SIZE", 16 * 1024 * 1024)
    # MAX_FORM_PARTS: Maximum number of form fields (default 1000)
    max_form_parts = _env_int("MAX_FORM_PARTS", 1000)
    # SECRET_KEY_FALLBACKS: Comma-separated list of fallback secret keys for rotation
    secret_key_fallbacks_str = os.getenv("SECRET_KEY_FALLBACKS", "")
    secret_key_fallbacks = tuple(key.strip() for key in secret_key_fallbacks_str.split(",") if key.strip())

    security = SecurityConfig(
        max_content_length=max_content_length,
        max_form_memory_size=max_form_memory_size,
        max_form_parts=max_form_parts,
        secret_key_fallbacks=secret_key_fallbacks,
    )

    return Settings(
        is_localhost=is_localhost,
        paths=_get_paths(),
        database_data=_load_db_data_new(),
        STATE_SESSION_KEY=STATE_SESSION_KEY,
        REQUEST_TOKEN_SESSION_KEY=REQUEST_TOKEN_SESSION_KEY,
        secret_key=secret_key,
        oauth_encryption_key=oauth_encryption_key,
        cookie=cookie,
        oauth=oauth_config,
        disable_uploads=os.getenv("DISABLE_UPLOADS", ""),
        download=DownloadConfig(dev_limit=dev_download_limit),
        security=security,
        csrf_time_limit=csrf_time_limit,
        dynamic=DynamicSettingsStore(_load_db_data_new()),
    )


settings = get_settings()
