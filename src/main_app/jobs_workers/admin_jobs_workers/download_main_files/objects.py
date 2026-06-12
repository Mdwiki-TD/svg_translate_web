"""Objects for download_main_files worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class DownloadMainFilesWorkerObject(StandardAdminWorkerObject):
    output_path: Optional[str] = None
    files_downloaded: list[dict[str, Any]] = field(default_factory=list)
    files_failed: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "DownloadMainFilesWorkerObject",
]
