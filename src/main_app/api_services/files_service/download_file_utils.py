"""Download task helper with progress callbacks."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests

from ..clients import CommonsSession

logger = logging.getLogger(__name__)

BASE_COMMONS_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/"


@dataclass
class DownloadResult:
    success: bool = False
    size_bytes: int | None = None
    path: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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
    overwrite_download: bool = True,
) -> dict[str, str]:
    """Download a single Commons file, skipping already-downloaded copies.

    Parameters:
        title (str): Title of the file page on Wikimedia Commons.
        out_dir (Path): Directory where the file should be stored.
        i (int): 1-based index used only for logging context.
        session (requests.Session | None): Optional shared session. A new session
            with an appropriate User-Agent is created when omitted.
        overwrite_download (bool): Whether to overwrite existing files.

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

    if out_path.exists() and not overwrite_download:
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


def download_svg_file(
    filename: str,
    temp_dir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Download SVG file and return file path or error info."""
    logger.info(f"Downloading file: {filename}")

    file_data = download_one_file(
        title=filename,
        out_dir=temp_dir,
        overwrite_download=True,
        session=session,
    )

    if file_data.get("result") != "success":
        return {
            "ok": False,
            "path": None,
            "error": "download_failed",
            "details": file_data,
        }
    return {
        "ok": True,
        "path": Path(file_data["path"]),
        "error": None,
        "details": {},
    }


def run_download_file(
    filename: str,
    output_dir: Path,
    session: requests.Session,
) -> DownloadResult:
    """
    Download a single file from Wikimedia Commons.

    Args:
        filename: The file name (e.g., "File:Example.svg")
        output_dir: Directory where the file should be saved
        session: requests session to use
    """
    result = {
        "success": False,
        "path": None,
        "size_bytes": None,
        "error": None,
    }

    if not filename:
        return DownloadResult(error="Empty filename")

    # Extract just the filename part (remove "File:" prefix if present)
    clean_filename = filename.removeprefix("File:")

    # Determine output path - maintain original filename
    out_path = output_dir / clean_filename

    # Use the core download function
    try:
        content = download_commons_file_core(clean_filename, session, timeout=60)
    except Exception as e:
        result["error"] = f"Download failed: {str(e)}"
        logger.exception("Failed to download %s", clean_filename)
        return DownloadResult(error=f"Download failed: {str(e)}")

    try:
        # Save the file
        out_path.write_bytes(content)
        file_size = len(content)

        result["success"] = True
        result["path"] = str(out_path.name)
        result["size_bytes"] = file_size
        logger.info("Downloaded: %s (%d bytes)", clean_filename, file_size)
        return DownloadResult(success=True, path=str(out_path.name), size_bytes=file_size)

    except Exception as e:
        result["error"] = f"Unexpected error: {str(e)}"
        logger.exception("Error saving %s", clean_filename)

        return DownloadResult(error=f"Unexpected error: {str(e)}")


__all__ = [
    "download_one_file",
    "download_svg_file",
    "run_download_file",
]
