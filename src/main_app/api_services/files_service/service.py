import logging
from pathlib import Path

import requests

from ..clients import create_commons_session
from .downloader import download_and_save
from .file_langs import get_file_languages
from .files_helpers import get_file_info
from .objects import (
    DownloadAndSaveData,
    FileInfo,
    FileLanguagesMap,
)

logger = logging.getLogger(__name__)


class FilesService:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session: requests.Session = session or create_commons_session()

    def get_file_info(self, title: str) -> FileInfo:
        """Get file info from Commons."""
        return get_file_info(title)

    def get_file_languages(self, title: str) -> FileLanguagesMap:
        """Get file languages from Commons."""
        return get_file_languages(title, self.session)

    # ----------------------
    #  download methods
    # ----------------------

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
