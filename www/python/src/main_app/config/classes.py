"""Application configuration helpers."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


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


def resolve_path(_path: str) -> Path:
    """Expand environment variables and user home directory in paths."""
    _path = os.path.expandvars(str(_path))
    path = Path(_path).expanduser()
    return path


# --- Data Classes for Configuration Sections ---


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
            name=os.getenv("AUTH_COOKIE_NAME", "uid_enc"),
            max_age=_env_int("AUTH_COOKIE_MAX_AGE", 30 * 24 * 3600),
            secure=session_cookie_secure,
            httponly=session_cookie_httponly,
            samesite=session_cookie_samesite,
        )

        return cookie


@dataclass(frozen=True)
class OtherConfig:
    """configs not in specific sections"""

    csrf_time_limit: int | None  # None means never expire
    user_agent: str
    static_server: str
    tool_title: str
    wiki_domain: str

    @property
    def full_wiki_domain(self) -> str:
        return f"https://{self.wiki_domain}"

    @classmethod
    def load(cls) -> OtherConfig:
        # CSRF token lifetime (in seconds). Default 3600 (1 hour).
        # Set to 0 or None to disable expiration (not recommended for production).
        csrf_time_limit = _env_int("WTF_CSRF_TIME_LIMIT", 3600)
        if not csrf_time_limit or csrf_time_limit <= 0:
            csrf_time_limit = 3600

        static_server = os.getenv("STATIC_SERVER") or "https://tools-static.wmflabs.org/cdnjs"

        user_agent = os.getenv(
            "USER_AGENT",
            "mytool/1.0 (https://mytool.toolforge.org; tools.mytool@toolforge.org)",
        )
        wiki_domain = os.getenv("WIKI_DOMAIN") or "commons.wikimedia.org"

        tool_title = os.getenv("TOOL_TITLE") or "Copy SVG Translations"

        return OtherConfig(
            csrf_time_limit=csrf_time_limit,
            user_agent=user_agent,
            static_server=static_server,
            tool_title=tool_title,
            wiki_domain=wiki_domain,
        )


@dataclass(frozen=True)
class JobsConfig:
    """Configuration for jobs."""

    jobs_max_workers: int
    jobs_log_lines: int
    priority_per_item: int | None = None
    backend: str = "thread"  # 'thread' or 'toolforge'
    toolforge_job_image: str = "python3.13"
    toolforge_job_default_memory: str = "1Gi"
    toolforge_job_default_cpu: str = "0.5"
    toolforge_job_script: str = "~/shs/flask_cmd.sh"

    @classmethod
    def load(cls) -> JobsConfig:
        # Background job runner sizing.
        jobs_max_workers = max(1, _env_int("JOBS_MAX_WORKERS", 2))
        jobs_log_lines = max(10, _env_int("JOBS_LOG_LINES", 200))

        priority_per_item = _env_int("PRIORITY_PER_ITEM", 0, safe=True)
        if priority_per_item == 0:
            priority_per_item = None

        backend = os.getenv("JOBS_BACKEND", "thread").strip().lower()
        if backend not in ("thread", "toolforge"):
            logger.warning("Unknown JOBS_BACKEND '%s', falling back to 'thread'", backend)
            backend = "thread"

        _config = JobsConfig(
            jobs_max_workers=jobs_max_workers,
            jobs_log_lines=jobs_log_lines,
            priority_per_item=priority_per_item,
            backend=backend,
            toolforge_job_image=os.getenv("TOOLFORGE_JOB_IMAGE", "python3.13"),
            toolforge_job_default_memory=os.getenv("TOOLFORGE_JOB_DEFAULT_MEMORY", "1Gi"),
            toolforge_job_default_cpu=os.getenv("TOOLFORGE_JOB_DEFAULT_CPU", "0.5"),
            toolforge_job_script=os.getenv("TOOLFORGE_JOB_SCRIPT", "~/shs/flask_cmd.sh"),
        )

        return _config


@dataclass(frozen=True)
class Paths:
    flask_data_dir: Path
    log_dir: Path
    jobs_path: Path
    admin_jobs_path: Path

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> Paths:
        """
        Compute the filesystem paths the application will use.

        The paths are rooted at the MAIN_DIR environment variable if set, otherwise at the user's ~/data directory.

        Returns:
            Paths: A dataclass
        """
        flask_data_dir = os.getenv("MAIN_DIR") or "~/data"
        flask_data_dir = resolve_path(flask_data_dir)

        return Paths(
            flask_data_dir=flask_data_dir,
            log_dir=flask_data_dir / "logs",
            jobs_path=flask_data_dir / "public_jobs",
            admin_jobs_path=flask_data_dir / "admin_jobs",
        )

    def all_paths(self) -> list[Path]:
        return [
            self.log_dir,
            self.jobs_path,
            self.admin_jobs_path,
        ]


@dataclass(frozen=True)
class CorsConfig:
    allowed_domains: list[str]

    @classmethod
    def load(cls) -> CorsConfig:
        # Load CORS configuration
        cors_domains_str = os.getenv("CORS_ALLOWED_DOMAINS", "")
        cors_domains = [d.strip() for d in cors_domains_str.split(",") if d.strip()]

        if not cors_domains:
            cors_domains = [
                "mdwikicx.toolforge.org",
                "mdwiki.toolforge.org",
            ]
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
        secret_key = os.getenv("FLASK_SECRET_KEY", "")

        if not secret_key:
            raise RuntimeError("FLASK_SECRET_KEY environment variable is required")

        # MAX_CONTENT_LENGTH: Maximum request size (default 100MB)
        max_content_length = _env_int("MAX_CONTENT_LENGTH", 100 * 1024 * 1024)

        # MAX_FORM_MEMORY_SIZE: Maximum form data in memory (default 16MB)
        max_form_memory_size = _env_int("MAX_FORM_MEMORY_SIZE", 16 * 1024 * 1024)

        # MAX_FORM_PARTS: Maximum number of form fields (default 1000)
        max_form_parts = _env_int("MAX_FORM_PARTS", 1000)

        # SECRET_KEY_FALLBACKS: Comma-separated list of fallback secret keys for rotation
        secret_key_fallbacks_str = os.getenv("SECRET_KEY_FALLBACKS", "")
        secret_key_fallbacks = tuple(key.strip() for key in secret_key_fallbacks_str.split(",") if key.strip())

        secret_salt = os.getenv("SECRET_SALT", "svg-translate")

        security_config = SecurityConfig(
            salt=secret_salt,
            secret_key=secret_key,
            max_content_length=max_content_length,
            max_form_memory_size=max_form_memory_size,
            max_form_parts=max_form_parts,
            secret_key_fallbacks=secret_key_fallbacks,
        )

        return security_config


@dataclass(frozen=True)
class Settings:
    """Main settings container."""

    # Nested configurations
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
            security=SecurityConfig.load(),
            paths=Paths.load(),
            cookie=CookieConfig.load(),
            oauth=OAuthConfig.load(),
            sessions=SessionConfig.load(),
            other=OtherConfig.load(),
            jobs=JobsConfig.load(),
            # cors=CorsConfig.load(),
        )

    def ensure_directories(self) -> None:
        """Create application directories if they don't exist.

        Call this once at app startup (in the factory), not at import time.
        """
        for dir_name in self.paths.all_paths():
            dir_name.mkdir(parents=True, exist_ok=True)


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
    return Settings.load()


__all__ = [
    "CookieConfig",
    "CorsConfig",
    "JobsConfig",
    "OAuthConfig",
    "OtherConfig",
    "Paths",
    "SecurityConfig",
    "SessionConfig",
    "Settings",
    "get_settings",
]
