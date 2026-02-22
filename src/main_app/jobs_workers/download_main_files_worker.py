"""
Worker module for downloading main files.
"""

from __future__ import annotations

import logging
import threading
from typing import Any
logger = logging.getLogger("svg_translate")


def download_main_files_for_templates(
    job_id: int, user: Any | None, cancel_event: threading.Event | None = None
) -> None:
    ...


__all__ = [
    "download_main_files_for_templates",
]
