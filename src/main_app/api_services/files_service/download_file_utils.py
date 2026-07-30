"""Download task helper with progress callbacks."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import quote

import requests

from ..clients import CommonsSession

logger = logging.getLogger(__name__)

BASE_COMMONS_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def download_commons_file_core(
    filename: str,
    session: requests.Session,
    timeout: int = 60,
) -> bytes:
    """
    Download a file from Wikimedia Commons and return raw content.

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

    bot = CommonsSession(session, timeout=timeout)
    response = bot.request(
        method="GET",
        url=url,
    )
    response.raise_for_status()
    return response.content


def download_file_rate_limit(
    filename: str,
    session: requests.Session | None = None,
    timeout: int = 60,
    max_attempts: int = 5,
) -> bytes | None:
    """
    Download a file from Wikimedia Commons and return raw content.
    """
    # Normalize filename: convert spaces to underscores for URL
    normalized_name = filename.replace(" ", "_")
    url = f"{BASE_COMMONS_URL}{quote(normalized_name)}"

    bot = CommonsSession(session, timeout=timeout)

    try:
        response = bot.get_with_retry(url=url, max_attempts=max_attempts)
        if response:
            return response.content
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")

    return None


def download_one_file(
    title: str,
    out_dir: Path,
    i: int = 0,
    session: requests.Session | None = None,
    overwrite: bool = False,
) -> dict[str, str]:
    """Download a single Commons file, skipping already-downloaded copies.

    Parameters:
        title (str): Title of the file page on Wikimedia Commons.
        out_dir (Path): Directory where the file should be stored.
        i (int): 1-based index used only for logging context.
        session (requests.Session | None): Optional shared session. A new session
            with an appropriate User-Agent is created when omitted.
        overwrite (bool): Whether to overwrite existing files.

    Returns:
        dict: Outcome dictionary with keys ``result`` ("success", "existing", or
        "failed") and ``path`` (path string when available).
    """
    data = {
        "result": "",
        "msg": "",
        "path": "",
    }

    if not title:
        return data

    out_path = out_dir / title

    if out_path.exists() and not overwrite:
        logger.debug(f"[{i}] Skipped existing: {title}")
        data["result"] = "existing"
        data["msg"] = "Skip existing file, no overwrite"
        data["path"] = str(out_path)
        return data

    # Use the core download function with shorter timeout
    try:
        content = download_file_rate_limit(title, session, timeout=30, max_attempts=5)
        if not content:
            raise Exception("Empty content")
    except Exception as e:
        data["result"] = "failed"
        logger.error(f"[{i}] Failed: {title} -> {e}")
        if "404 Client Error: Not Found for url" in str(e):
            data["msg"] = "File not found"
        return data

    try:
        out_path.write_bytes(content)
        logger.debug(f"[{i}] Downloaded: {title}")
        data["result"] = "success"
        data["path"] = str(out_path)
    except Exception as e:
        data["result"] = "failed"
        data["msg"] = f"Failed to save file: {e}"
        logger.error(f"[{i}] Failed to save: {title} -> {e}")

    return data


__all__ = [
    "download_one_file",
]
