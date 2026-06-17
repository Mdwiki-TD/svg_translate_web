from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests
from mwclient.client import Site

from .upload_bot import upload_file
from .utils import download_one_file

logger = logging.getLogger(__name__)


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
        i=1,
        overwrite=True,
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


def upload_fixed_svg(
    filename: str,
    file_path: Path,
    tags_fixed: int,
    site: Site,
) -> dict[str, Any]:
    """Upload fixed SVG file to Commons."""

    logger.info(f"Uploading fixed file: {filename}")

    result = upload_file(
        file_name=filename,
        file_path=file_path,
        site=site,
        summary=f"Fixed {tags_fixed} nested tag(s)",
    )

    if result.get("result") != "Success":
        return {
            "ok": False,
            "error": result.get("error", "upload_failed"),
            "error_details": result.get("error_details", ""),
            "result": None,
        }

    return {
        "ok": True,
        "error": None,
        "error_details": None,
        "result": result,
    }


__all__ = [
    "download_svg_file",
    "upload_fixed_svg",
]
