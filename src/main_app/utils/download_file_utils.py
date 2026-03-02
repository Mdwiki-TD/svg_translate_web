"""Download task helper with progress callbacks."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict

import requests

from ..config import settings
from .commons_client import create_commons_session, download_commons_file_core

logger = logging.getLogger(__name__)


def download_one_file(
    title: str,
    out_dir: Path,
    i: int,
    session: requests.Session = None,
    overwrite: bool = False,
) -> Dict[str, str]:
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

    if not session:
        session = create_commons_session(settings.oauth.user_agent)

    # Use the core download function with shorter timeout
    try:
        content = download_commons_file_core(title, session, timeout=30)
    except Exception as e:
        data["result"] = "failed"
        logger.error(f"[{i}] Failed: {title} -> {e}")
        if "404 Client Error: Not Found for url" in str(e):
            data["msg"] = "File not found"
        # 2026-03-02 02:28:16,694 - main_app.utils.download_file_utils - ERROR [1] Failed: share with mental and substance disorders, World, 2021zz.svg -> 404 Client Error: Not Found for url: https://commons.wikimedia.org/wiki/Special:Redirect/file/share_with_mental_and_substance_disorders,_World,_2021zz.svg
        return data

    try:
        out_path.write_bytes(content)
        logger.debug(f"[{i}] Downloaded: {title}")
        data["result"] = "success"
        data["path"] = str(out_path)
    except Exception as e:
        data["result"] = "failed"
        data["msg"] = ""
        logger.error(f"[{i}] Failed to save: {title} -> {e}")

    return data


def download_commons_svgs(titles, files_dir):
    files = []
    for n, title in enumerate(titles, 1):
        file = download_one_file(title, files_dir, n)
        if file.get("path"):
            files.append(file["path"])
    return files
