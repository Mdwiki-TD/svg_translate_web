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
    FileInfo,
)
from .upload_bot import UploadFile

logger = logging.getLogger(__name__)


def _download_svg_file(
    filename: str,
    temp_dir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Download SVG file and return file path or error info."""
    logger.info(f"Downloading file: {filename}")

    file_data = download_one_file(
        title=filename,
        out_dir=temp_dir,
        overwrite_download=True,
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

def _upload_fixed_svg(
    filename: str,
    file_path: Path,
    site: Site,
    summary: str,
) -> dict[str, Any]:
    """Upload SVG file to Commons."""

    logger.info(f"Uploading file: {filename}")

    if not site:
        return {
            "ok": False,
            "error": "No site provided",
            "error_details": "",
            "msg": None,
            "result": None,
        }
    bot = UploadFile(
        file_name=filename,
        file_path=file_path,
        site=site,
        summary=summary,
    )
    result = bot.upload()

    result_status = result.get("result") or ""
    error_details = result.get("error_details", "")
    result_error = result.get("error", "upload_failed")

    if result_status.lower() == "success":
        return {
            "ok": True,
            "error": None,
            "error_details": error_details,
            "msg": None,
            "result": result,
        }

    if result_error == "fileexists-no-change" or result_status == "fileexists-no-change":
        return {
            "ok": None,
            "error": "skipped",
            "error_details": error_details,
            "msg": "File already exists with same content",
            "result": None,
        }

    return {
        "ok": False,
        "error": result_error,
        "error_details": error_details,
        "msg": None,
        "result": None,
    }


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
        return _download_svg_file(
            filename=filename,
            temp_dir=temp_dir,
            session=self.session,
        )

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

    def upload_fixed_svg(
        self,
        filename: str,
        file_path: Path,
        summary: str,
    ) -> dict[str, Any]:
        """Upload a fixed SVG to Commons."""
        return _upload_fixed_svg(
            filename=filename,
            file_path=file_path,
            site=self.site,
            summary=summary,
        )

    def upload_file(
        self,
        file_name: str,
        file_path: Path,
        summary: str | None = None,
        description: str | None = None,
        new_file: bool = False,
    ) -> dict:
        uploader = UploadFile(
            file_name=file_name,
            file_path=file_path,
            site=self.site,
            summary=summary,
            description=description,
            new_file=new_file,
        )

        return uploader.upload()
