"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional


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
class Settings:
    is_localhost: callable
    database_data: DbConfig
    STATE_SESSION_KEY: str
    REQUEST_TOKEN_SESSION_KEY: str
    secret_key: str
    use_mw_oauth: bool
    oauth_encryption_key: Optional[str]
    cookie: CookieConfig
    oauth: Optional[OAuthConfig]
    paths: Paths
    disable_uploads: str


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
    """
    main_dir = os.getenv("MAIN_DIR", os.path.join(os.path.expanduser("~"), "data"))
    svg_data = f"{main_dir}/svg_data"
    svg_data_thumb = f"{main_dir}/svg_data_thumb"
    log_dir = f"{main_dir}/logs"
    fix_nested_data = f"{main_dir}/fix_nested_data"
    svg_jobs_path = f"{main_dir}/svg_jobs"

    # Ensure directories exist
    Path(svg_data).mkdir(parents=True, exist_ok=True)
    Path(svg_data_thumb).mkdir(parents=True, exist_ok=True)
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    Path(fix_nested_data).mkdir(parents=True, exist_ok=True)
    Path(svg_jobs_path).mkdir(parents=True, exist_ok=True)

    return Paths(
        svg_data=svg_data,
        svg_data_thumb=svg_data_thumb,
        log_dir=log_dir,
        fix_nested_data=fix_nested_data,
        svg_jobs_path=svg_jobs_path,
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
        RuntimeError: If USE_MW_OAUTH is enabled but OAUTH_ENCRYPTION_KEY is missing.
        RuntimeError: If USE_MW_OAUTH is enabled but the OAuth configuration (OAUTH_MWURI, OAUTH_CONSUMER_KEY, OAUTH_CONSUMER_SECRET) is incomplete.
    """
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("FLASK_SECRET_KEY environment variable is required")

    session_cookie_secure = _env_bool("SESSION_COOKIE_SECURE", default=True)
    session_cookie_httponly = _env_bool("SESSION_COOKIE_HTTPONLY", default=True)
    session_cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    STATE_SESSION_KEY = os.getenv("STATE_SESSION_KEY", "oauth_state_nonce")
    REQUEST_TOKEN_SESSION_KEY = os.getenv("REQUEST_TOKEN_SESSION_KEY", "state")

    use_mw_oauth = _env_bool("USE_MW_OAUTH", default=True)
    oauth_config = _load_oauth_config()

    oauth_encryption_key = os.getenv("OAUTH_ENCRYPTION_KEY")
    if use_mw_oauth and not oauth_encryption_key:
        raise RuntimeError("OAUTH_ENCRYPTION_KEY environment variable is required when USE_MW_OAUTH is enabled")

    cookie = CookieConfig(
        name=os.getenv("AUTH_COOKIE_NAME", "uid_enc"),
        max_age=_env_int("AUTH_COOKIE_MAX_AGE", 30 * 24 * 3600),
        secure=session_cookie_secure,
        httponly=session_cookie_httponly,
        samesite=session_cookie_samesite,
    )

    if use_mw_oauth and oauth_config is None:
        raise RuntimeError(
            "MediaWiki OAuth configuration is incomplete. Set OAUTH_MWURI, OAUTH_CONSUMER_KEY, and OAUTH_CONSUMER_SECRET."
        )

    return Settings(
        is_localhost=is_localhost,
        paths=_get_paths(),
        database_data=_load_db_data_new(),
        STATE_SESSION_KEY=STATE_SESSION_KEY,
        REQUEST_TOKEN_SESSION_KEY=REQUEST_TOKEN_SESSION_KEY,
        secret_key=secret_key,
        use_mw_oauth=use_mw_oauth,
        oauth_encryption_key=oauth_encryption_key,
        cookie=cookie,
        oauth=oauth_config,
        disable_uploads=os.getenv("DISABLE_UPLOADS", ""),
    )


settings = get_settings()
