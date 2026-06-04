"""Application configuration helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .classes import (
    CookieConfig,
    DbConfig,
    JobsConfig,
    OAuthConfig,
    OtherConfig,
    Paths,
    SecurityConfig,
    SessionConfig,
    Settings,
)

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


# --- Configuration Loaders ---


def _load_security_config() -> SecurityConfig:
    """
    Load security configuration (Flask 3.1+ features)
    """
    # MAX_CONTENT_LENGTH: Maximum request size (default 100MB for SVG uploads)
    max_content_length = _env_int("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)

    # MAX_FORM_MEMORY_SIZE: Maximum form data in memory (default 16MB)
    max_form_memory_size = _env_int("MAX_FORM_MEMORY_SIZE", 16 * 1024 * 1024)

    # MAX_FORM_PARTS: Maximum number of form fields (default 1000)
    max_form_parts = _env_int("MAX_FORM_PARTS", 1000)

    # SECRET_KEY_FALLBACKS: Comma-separated list of fallback secret keys for rotation
    secret_key_fallbacks_str = os.getenv("SECRET_KEY_FALLBACKS", "")
    secret_key_fallbacks = tuple(key.strip() for key in secret_key_fallbacks_str.split(",") if key.strip())

    secret_key = os.getenv("FLASK_SECRET_KEY", "")

    security_config = SecurityConfig(
        secret_key=secret_key,
        max_content_length=max_content_length,
        max_form_memory_size=max_form_memory_size,
        max_form_parts=max_form_parts,
        secret_key_fallbacks=secret_key_fallbacks,
    )
    return security_config


def _load_database_config() -> DbConfig:
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


def _load_oauth_config() -> OAuthConfig:
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
            - jobs_path: path for SVG job files
            - main_files_path: path for main files
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
    return Paths(**_dirs)


def load_other_config() -> OtherConfig:
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
    _config = OtherConfig(
        csrf_time_limit=csrf_time_limit,
        user_agent=user_agent,
        wiki_domain=wiki_domain,
        static_server=static_server,
    )

    return _config


def load_cookie_config() -> CookieConfig:
    session_cookie_secure = _env_bool("SESSION_COOKIE_SECURE", default=True)
    session_cookie_httponly = _env_bool("SESSION_COOKIE_HTTPONLY", default=True)
    session_cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    cookie = CookieConfig(
        name=os.getenv("AUTH_COOKIE_NAME", "uid_enc"),
        max_age=_env_int("AUTH_COOKIE_MAX_AGE", 30 * 24 * 3600),
        secure=session_cookie_secure,
        httponly=session_cookie_httponly,
        samesite=session_cookie_samesite,
    )

    return cookie


def _load_jobs_config() -> JobsConfig:
    # Load download configuration
    priority_per_item = _env_int("PRIORITY_PER_ITEM", None, safe=True)

    _config = JobsConfig(
        disable_uploads=os.getenv("DISABLE_UPLOADS", ""),
        upload_host=os.getenv("UPLOAD_END_POINT", "commons.wikimedia.org"),
        priority_per_item=priority_per_item,
    )

    return _config


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
    sessions = SessionConfig(
        state_key=os.getenv("STATE_SESSION_KEY", "oauth_state_nonce"),
        request_token_key=os.getenv("REQUEST_TOKEN_SESSION_KEY", "state"),
    )
    security_config = _load_security_config()

    if not security_config.secret_key:
        raise RuntimeError("FLASK_SECRET_KEY environment variable is required")

    oauth_config = _load_oauth_config()

    cookie_config = load_cookie_config()

    other_config = load_other_config()

    database_data = _load_database_config()
    jobs_config = _load_jobs_config()

    return Settings(
        paths=_get_paths(),
        database_data=database_data,
        cookie=cookie_config,
        oauth=oauth_config,
        security=security_config,
        sessions=sessions,
        jobs=jobs_config,
        other=other_config,
    )


# Singleton settings instance
settings = get_settings()


def ensure_directories() -> None:
    """Create application directories if they don't exist.

    Call this once at app startup (in the factory), not at import time.
    """
    for dir_name in [
        settings.paths.log_dir,
        settings.paths.jobs_path,
        settings.paths.main_files_path,
        settings.paths.svg_data,
        settings.paths.svg_data_thumb,
        settings.paths.fix_nested_data,
        settings.paths.crop_main_files_path,
    ]:
        Path(dir_name).mkdir(parents=True, exist_ok=True)


__all__ = [
    "ensure_directories",
    "settings",
]
