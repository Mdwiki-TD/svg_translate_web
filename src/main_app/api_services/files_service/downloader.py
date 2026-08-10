"""Download task helper with progress callbacks."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import quote

import requests

from ..clients import CommonsSession, GetWithRetryData
from .objects import DownloadAndSaveData

logger = logging.getLogger(__name__)

BASE_COMMONS_URL = "https://commons.wikimedia.org/wiki/Special:FilePath/"


def _save_file(content: bytes, out_path: Path):
    try:
        out_path.write_bytes(content)
        return True, None
    except Exception as e:
        logger.error(f"Failed to save: {str(out_path)} -> {e}")
        return False, e


def download(
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
        session (requests.Session | None): Optional shared session. A new session
            with an appropriate User-Agent is created when omitted.
        overwrite_download (bool): Whether to overwrite existing files.
    """

    if not title:
        return DownloadAndSaveData(result="failed", msg="Empty title provided")

    out_path = out_dir / title

    if out_path.exists() and not overwrite_download:
        logger.debug(f"Skipped existing: {title}")
        return DownloadAndSaveData(
            result="existing",
            msg="Skip existing file, no overwrite",
            path=str(out_path),
        )

    # download part
    def _download_it(title) -> GetWithRetryData:
        normalized_name = title.replace(" ", "_")
        url = f"{BASE_COMMONS_URL}{quote(normalized_name)}"

        downloader = CommonsSession(session, timeout=30)
        result = downloader.get_with_retry_obj(url=url, max_attempts=5)

        return result

    # Use the core download function with shorter timeout
    try:
        download_result = _download_it(title)
    except Exception as e:
        logger.error(f"Failed: {title} -> {e}")
        return DownloadAndSaveData(result="failed")

    if download_result.status_code != 200:
        logger.error(f"Failed: {title} -> {download_result.status_code}")
        return DownloadAndSaveData(result="failed", msg=download_result.msg, error=download_result.msg)

    content = download_result.content
    if content is None:
        logger.error(f"Failed: {title} -> No content")
        return DownloadAndSaveData(result="failed", msg=download_result.msg, error=download_result.msg)

    # save part
    saved, save_error = _save_file(content, out_path)
    if saved:
        return DownloadAndSaveData(result="success", path=str(out_path))
    else:
        msg = f"Failed to save file: {save_error}"
        return DownloadAndSaveData(result="failed", msg=msg, error=msg)


__all__ = [
    "DownloadAndSaveData",
    "download",
]
