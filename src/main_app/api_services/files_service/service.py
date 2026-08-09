from pathlib import Path
from typing import Any

import requests
from mwclient.client import Site

from ..clients import create_commons_session
from .download_file_utils import (
    DownloadResult,
    download_one_file,
    download_svg_file,
    run_download_file,
)
from .files_helpers import FileInfo, get_file_info
from .upload_bot import (
    UploadFile,
    upload_fixed_svg,
)


class FilesService:
    def __init__(self, site: Site, session: requests.Session | None = None) -> None:
        self.site: Site = site
        self.session: requests.Session = session or create_commons_session()

    def get_file_info(self, title: str) -> FileInfo:
        """Get file info from Commons."""
        return get_file_info(title)

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
        return upload_fixed_svg(
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

    # ----------------------
    #  download methods
    # ----------------------

    def download_one_file(
        self,
        title: str,
        out_dir: Path,
        i: int = 0,
        overwrite_download: bool = True,
    ) -> dict[str, str]:
        """Download a file from Commons and upload it to Commons."""
        return download_one_file(
            title=title,
            out_dir=out_dir,
            i=i,
            session=self.session,
            overwrite_download=overwrite_download,
        )

    def download_svg_file(
        self,
        filename: str,
        temp_dir: Path,
    ) -> dict[str, Any]:
        return download_svg_file(
            filename=filename,
            temp_dir=temp_dir,
            session=self.session,
        )

    def run_download_file(
        self,
        filename: str,
        output_dir: Path,
        session: requests.Session,
    ) -> DownloadResult:
        return run_download_file(
            filename=filename,
            output_dir=output_dir,
            session=session,
        )
