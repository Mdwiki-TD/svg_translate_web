"""
Worker module for downloading main files from remote source to local filesystem.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import send_file

logger = logging.getLogger(__name__)

# Zip file name constant
MAIN_FILES_ZIP_NAME = "main_files.zip"


class ZipProvider:
    def __init__(
        self,
        main_files_path: Path,
    ) -> None:
        self.main_files_path = Path(main_files_path)
        self.zip_file_path = self.main_files_path / MAIN_FILES_ZIP_NAME

    def create_main_files_zip(self) -> tuple[Any, int]:
        """
        Serve the main files zip archive.

        Checks for an existing zip file first. If it doesn't exist, returns an error.
        The zip file should be generated automatically when a download job completes successfully.

        Returns:
            tuple: (send_file response or error message, status_code)
        """

        if not self.main_files_path.is_dir():
            return "Main files directory does not exist", 404

        # Check if zip file exists
        if not self.zip_file_path.exists():
            return "Zip file not found. Please run a 'Download Main Files' job first to generate the archive.", 404

        # Check if zip file is valid (not empty)
        if self.zip_file_path.stat().st_size == 0:
            return "Zip file is empty or corrupted. Please re-run the 'Download Main Files' job.", 500

        return (
            send_file(
                self.zip_file_path,
                mimetype="application/zip",
                as_attachment=True,
                download_name=MAIN_FILES_ZIP_NAME,
            ),
            200,
        )


__all__ = [
    "ZipProvider",
    "MAIN_FILES_ZIP_NAME",
]
