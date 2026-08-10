import logging
from pathlib import Path
from typing import Any

import requests
from mwclient.client import Site

from ..clients import create_commons_session
from .download_file_utils import (
    download_one_file,
)
from .downloader import download_and_save
from .files_helpers import get_file_info
from .objects import (
    DownloadAndSaveData,
    DownloadResult2,
    FileInfo,
    UploadResult,
)
from .upload_bot import UploadFile

logger = logging.getLogger(__name__)


def _download_svg_file(
    filename: str,
    temp_dir: Path,
    session: requests.Session | None = None,
) -> DownloadResult2:
    """Download SVG file and return file path or error info."""
    logger.info(f"Downloading file: {filename}")

    file_data = download_one_file(
        title=filename,
        out_dir=temp_dir,
        overwrite_download=True,
        session=session,
    )

    if file_data.get("result") != "success":
        return DownloadResult2(
            ok=False,
            path=None,
            error="download_failed",
            details=file_data,
        )
    return DownloadResult2(
        ok=True,
        path=Path(file_data["path"]),
        error=None,
        details={},
    )


class FilesService:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session: requests.Session = session or create_commons_session()

    def get_file_info(self, title: str) -> FileInfo:
        """Get file info from Commons."""
        return get_file_info(title)

    # ----------------------
    #  download methods
    # ----------------------

    def download_one_file(
        self,
        title: str,
        out_dir: Path,
        overwrite_download: bool = True,
    ) -> dict[str, str]:
        """Download a file from Commons and save it to out_dir."""
        return download_one_file(
            title=title,
            out_dir=out_dir,
            session=self.session,
            overwrite_download=overwrite_download,
        )

    def download_svg_file(
        self,
        filename: str,
        temp_dir: Path,
    ) -> dict[str, Any]:
        result = _download_svg_file(
            filename=filename,
            temp_dir=temp_dir,
            session=self.session,
        )
        return result.to_json()

    def download_and_save(
        self,
        title: str,
        out_dir: Path,
        overwrite_download: bool = True,
    ) -> DownloadAndSaveData:
        """Download a file from Commons and save it to out_dir."""
        return download_and_save(
            title=title,
            out_dir=out_dir,
            session=self.session,
            overwrite_download=overwrite_download,
        )


class UploadService:
    def __init__(self, site: Site) -> None:
        self.site: Site = site

    # ----------------------
    #  upload methods
    # ----------------------

    def upload_svg(
        self,
        filename: str,
        file_path: Path,
        summary: str,
    ) -> UploadResult:
        """Upload SVG file to Commons."""
        logger.info(f"Uploading file: {filename}")

        bot = UploadFile(
            file_name=filename,
            file_path=file_path,
            site=self.site,
            summary=summary,
        )
        return bot.upload_obj()
