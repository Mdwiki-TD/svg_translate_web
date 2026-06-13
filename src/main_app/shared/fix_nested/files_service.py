from __future__ import annotations

import logging
from pathlib import Path

from ...api_services.utils import download_one_file
from .objects import DownloadResult

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


__all__ = [
    "download_svg_file",
]
