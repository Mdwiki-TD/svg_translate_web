"""Low-level Wikimedia Commons download utilities.

This module provides the core HTTP download functionality for fetching
files from Wikimedia Commons. It serves as the foundation for higher-level
download functions used across the application.
"""

from __future__ import annotations

import logging
from urllib.parse import quote

import requests

logger = logging.getLogger("svg_translate")

BASE_COMMONS_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def create_commons_session(user_agent: str | None = None) -> requests.Session:
    """Create a pre-configured requests Session for Commons API calls.

    Args:
        user_agent: Optional custom User-Agent string. If not provided,
            defaults to a generic bot identifier.

    Returns:
        Configured requests Session ready for use.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent or "SVGTranslateBot/1.0",
        }
    )
    return session


def download_commons_file_core(
    filename: str,
    session: requests.Session,
    timeout: int = 60,
) -> bytes:
    """Download a file from Wikimedia Commons and return raw content.

    This is the lowest-level download function that handles the actual HTTP
    request to Commons. It performs no file I/O or application-level validation;
    network and HTTP errors are raised as exceptions for callers to handle.

    Args:
        filename: Clean filename without "File:" prefix. Spaces will be
            converted to underscores for the URL.
        session: Pre-configured requests Session with appropriate headers
            (User-Agent, etc.).
        timeout: Request timeout in seconds. Defaults to 60s for compatibility
            with larger SVG files.

    Returns:
        Raw bytes content of the downloaded file.

    Raises:
        requests.RequestException: On network errors, HTTP errors (4xx, 5xx),
            or timeouts.

    Example:
        >>> session = create_commons_session("MyBot/1.0")
        >>> try:
        ...     content = download_commons_file_core("Example.svg", session)
        ...     Path("Example.svg").write_bytes(content)
        ... except requests.RequestException as e:
        ...     logger.error(f"Download failed: {e}")
    """
    # Normalize filename: convert spaces to underscores for URL
    normalized_name = filename.replace(" ", "_")
    url = f"{BASE_COMMONS_URL}{quote(normalized_name)}"

    response = session.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()
    return response.content


__all__ = [
    "download_commons_file_core",
    "create_commons_session",
]
