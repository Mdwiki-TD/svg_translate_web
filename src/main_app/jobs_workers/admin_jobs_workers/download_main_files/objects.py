"""
Objects for download_main_files worker.


"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class FileInfo:
    template_id: int
    template_title: str
    filename: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = ""
    reason: None | str = None
    error_type: None | str = None
    path: None | str = None
    size_bytes: None | int = None

    def to_dict(self) -> dict[str, Any]:
        """
        convert to dict.
        """
        return asdict(self)


@dataclass
class DownloadMainFilesWorkerObject(StandardAdminWorkerObject):
    output_path: Optional[str] = None
    files_downloaded: list[dict[str, Any]] = field(default_factory=list)
    files_failed: list[dict[str, Any]] = field(default_factory=list)


_old_result = {
    "note": "",
    "status": "pending",
    "errors": [],
    "args": {},
    "job_id": "self.job_id",
    "started_at": "datetime.now().isoformat()",
    "completed_at": None,
    "cancelled_at": None,
    "summary": {
        "total": 0,
        "processed": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
    },
    "output_path": "str(self.output_dir)",
    "files_downloaded": [],
    "files_failed": [],
}

__all__ = [
    "DownloadMainFilesWorkerObject",
]
