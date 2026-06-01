"""Application configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# --- Data Classes for Configuration Sections ---


@dataclass(frozen=True)
class OtherConfig:
    """configs not in specific sections"""

    csrf_time_limit: Optional[int]  # None means never expire
    user_agent: str
    wiki_domain: str
    static_server: str


@dataclass(frozen=True)
class JobsConfig:
    """Configuration for jobs."""

    dev_limit: int  # Limit for downloads in development mode (0 = unlimited)
    disable_uploads: str
    upload_host: str


@dataclass(frozen=True)
class DbConfig:
    db_name: str
    db_host: str
    db_user: str | None
    db_password: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "db_name": self.db_name,
            "db_host": self.db_host,
            "db_user": self.db_user,
            "db_password": self.db_password,
        }


@dataclass(frozen=True)
class Paths:
    log_dir: str
    jobs_path: str
    main_files_path: str
    svg_data: str
    svg_data_thumb: str
    fix_nested_data: str
    crop_main_files_path: str


@dataclass(frozen=True)
class CookieConfig:
    name: str
    max_age: int
    secure: bool
    httponly: bool
    samesite: str


@dataclass(frozen=True)
class SessionConfig:
    """Keys used for storing data in Flask session."""

    state_key: str
    request_token_key: str


@dataclass(frozen=True)
class OAuthConfig:
    """MediaWiki OAuth specific configuration."""

    mw_uri: str
    consumer_key: str
    consumer_secret: str
    encryption_key: str | None


@dataclass(frozen=True)
class CorsConfig:
    allowed_domains: list[str]


@dataclass(frozen=True)
class SecurityConfig:
    """Security configuration for Flask 3.1+ features."""

    secret_key: str
    max_content_length: int  # Maximum request size in bytes
    max_form_memory_size: int  # Maximum form data in memory in bytes
    max_form_parts: int  # Maximum number of form fields
    secret_key_fallbacks: tuple[str, ...]  # Fallback secret keys for rotation


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
