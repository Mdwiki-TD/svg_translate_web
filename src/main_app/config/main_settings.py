"""Application configuration helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .classes import Settings


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


# Singleton settings instance
settings = get_settings()


def ensure_directories() -> None:
    """Create application directories if they don't exist.

    Call this once at app startup (in the factory), not at import time.
    """
    for dir_name in settings.paths.all_paths():
        Path(dir_name).mkdir(parents=True, exist_ok=True)


__all__ = [
    "ensure_directories",
    "settings",
]
