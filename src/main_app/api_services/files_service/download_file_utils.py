"""Download task helper with progress callbacks."""

from __future__ import annotations

import logging
from pathlib import Path

import requests

from .downloader import download_and_save
from .objects import DownloadAndSaveData

logger = logging.getLogger(__name__)


def download_one_file(
    title: str,
    out_dir: Path,
    session: requests.Session | None = None,
    overwrite_download: bool = True,
    **kwargs,
) -> dict[str, str]:
    """
    Download a single Commons file, skipping already-downloaded copies.

    Parameters:
        title (str): Title of the file page on Wikimedia Commons.
        out_dir (Path): Directory where the file should be stored.
        session (requests.Session | None): Optional shared session. A new session
            with an appropriate User-Agent is created when omitted.
        overwrite_download (bool): Whether to overwrite existing files.

    Returns:
        dict: Outcome dictionary with keys ``result`` ("success", "existing", or
        "failed") and ``path`` (path string when available).
    """
    result = download_and_save(
        title=title,
        out_dir=out_dir,
        session=session,
        overwrite_download=overwrite_download,
    )

    return result.to_dict()


__all__ = [
    "DownloadAndSaveData",
    "download_one_file",
]
