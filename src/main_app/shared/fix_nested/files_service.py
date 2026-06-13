from __future__ import annotations

import logging
from pathlib import Path

from ...api_services import get_user_site, upload_file
from ...api_services.utils import download_one_file
from .objects import (
    DownloadResult,
    UploadResult,
)

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
    user,
) -> UploadResult:
    """Upload fixed SVG file to Commons."""
    if not user:
        return UploadResult(
            ok=False,
            error="unauthenticated",
        )

    site = get_user_site(user)

    if not site:
        return UploadResult(
            ok=False,
            error="oauth-auth-failed",
        )

    logger.info(f"Uploading fixed file: {filename}")

    result = upload_file(
        file_name=filename,
        file_path=file_path,
        site=site,
        summary=f"Fixed {tags_fixed} nested tag(s) using svg_translate_web",
    )

    if result.get("result") != "Success":
        return UploadResult(
            ok=False,
            error=result.get("error", "upload_failed"),
            error_details=result.get("error_details", ""),
        )

    return UploadResult(
        ok=True,
        result=result,
    )


__all__ = [
    "download_svg_file",
    "upload_fixed_svg",
]
