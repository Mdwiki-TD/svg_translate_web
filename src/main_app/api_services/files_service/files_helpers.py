from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests
from mwclient.client import Site

from ..upload_bot import upload_file
from . import download_one_file

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
    summary: str | None = None,
) -> dict[str, Any]:
    """Upload fixed SVG file to Commons."""

    logger.info(f"Uploading fixed file: {filename}")

    summary = summary or f"Fixed {tags_fixed} nested tag(s)"

    result = upload_file(
        file_name=filename,
        file_path=file_path,
        site=site,
        summary=summary,
    )
    result_status = result.get("result") or ""

    if result_status.lower() == "success":
        return {
            "ok": True,
            "error": None,
            "error_details": None,
            "msg": None,
            "result": result,
        }

    if result_status == "fileexists-no-change":
        return {
            "ok": None,
            "error": "skipped",
            "error_details": None,
            "msg": "File already exists with same content",
            "result": None,
        }

    return {
        "ok": False,
        "error": result.get("error", "upload_failed"),
        "error_details": result.get("error_details", ""),
        "msg": None,
        "result": None,
    }


__all__ = [
    "download_svg_file",
    "upload_fixed_svg",
]
