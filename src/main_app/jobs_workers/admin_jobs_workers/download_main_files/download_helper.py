""" """

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

from ....api_services.files_service import run_download_file

logger = logging.getLogger(__name__)


def download_file_from_commons(
    filename: str,
    output_dir: Path,
    session: requests.Session,
) -> dict[str, Any]:
    """
    Download a single file from Wikimedia Commons.

    Args:
        filename: The file name (e.g., "File:Example.svg")
        output_dir: Directory where the file should be saved
        session: requests session to use

    Returns:
        dict with keys:
            - success (bool)
            - path (str|None)
            - size_bytes (int|None)
            - error (str|None)
    """
    result = run_download_file(filename, output_dir, session)
    return result.to_dict()


__all__ = [
    "download_file_from_commons",
]
