"""Download task helper with progress callbacks."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import quote

import requests

from ..clients import CommonsSession, GetWithRetryData
from .objects import DownloadAndSaveData
from .save_file import write_bytes_to_file

logger = logging.getLogger(__name__)

BASE_COMMONS_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def download_and_save(
    *,
    title: str,
    out_dir: Path,
    session: requests.Session | None = None,
    overwrite_download: bool = True,
) -> DownloadAndSaveData:
    """
    Download a single Commons file, skipping already-downloaded copies.

    Parameters:
        title (str): Title of the file page on Wikimedia Commons.
        out_dir (Path): Directory where the file should be stored.
        session (requests.Session | None): Optional services session. A new session
            with an appropriate User-Agent is created when omitted.
        overwrite_download (bool): Whether to overwrite existing files.
    """

    if not title:
        return DownloadAndSaveData(result="failed", error="Empty title provided")

    clean_title = title.removeprefix("File:")
    out_path = out_dir / clean_title

    if out_path.exists() and not overwrite_download:
        logger.debug(f"Skipped existing: {title}")
        return DownloadAndSaveData(
            result="existing",
            error="Skip existing file, no overwrite",
            path=str(out_path),
        )

    # Use the core download function with shorter timeout
    try:
        normalized_name = title.replace(" ", "_")
        url = f"{BASE_COMMONS_URL}{quote(normalized_name)}"

        downloader = CommonsSession(session, timeout=30)
        download_result: GetWithRetryData = downloader.get_with_retry_obj(url=url, max_attempts=5)

    except Exception as e:
        logger.error(f"Failed: {title} -> {e}")
        return DownloadAndSaveData(result="failed")

    if download_result.status_code != 200:
        logger.error(f"Failed: {title} -> {download_result.status_code}")
        return DownloadAndSaveData(result="failed", error=download_result.msg)

    content = download_result.content
    if content is None:
        logger.error(f"Failed: {title} -> No content")
        return DownloadAndSaveData(result="failed", error=download_result.msg)

    size_bytes = len(content)

    # save part
    saved = write_bytes_to_file(content=content, filename=title, output_dir=out_dir)
    if saved.success:
        return DownloadAndSaveData(result="success", path=str(saved.path), size_bytes=size_bytes)
    else:
        msg = f"Failed to save file: {saved.error}"
        return DownloadAndSaveData(result="failed", error=msg, size_bytes=size_bytes)


__all__ = [
    "DownloadAndSaveData",
    "download_and_save",
]
