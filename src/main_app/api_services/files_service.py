from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mwclient.client import Site

from ..shared.fix_nested.objects import DownloadResult
from . import upload_file
from .utils import download_one_file

logger = logging.getLogger(__name__)


def download_svg_file(filename: str, temp_dir: Path) -> DownloadResult:
    """Download SVG file and return file path or error info."""
    logger.info(f"Downloading file: {filename}")

    file_data = download_one_file(
        title=filename,
        out_dir=temp_dir,
        i=1,
        overwrite=True,
    )

    if file_data.get("result") != "success":
        return DownloadResult(
            ok=False,
            error="download_failed",
            details=file_data,
        )

    return DownloadResult(
        ok=True,
        path=Path(file_data["path"]),
    )


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
        summary=f"Fixed {tags_fixed} nested tag(s) using svg_translate_web",
    )

    if result.get("result") != "Success":
        return {
            "ok": False,
            "error": result.get("error", "upload_failed"),
            "error_details": result.get("error_details", ""),
        }

    return {"ok": True, "result": result}


__all__ = [
    "download_svg_file",
    "upload_fixed_svg",
]
