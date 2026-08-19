"""
Objects for download_main_files worker.


"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from ....database.models import TemplateRecord
from ...shared_objects import StandardAdminWorkerObject


@dataclass
class FileInfo:
    template_id: int
    template_title: str
    filename: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = ""
    error: None | str = None
    error_type: None | str = None
    path: None | str = None
    size_bytes: None | int = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]

    @classmethod
    def from_template(cls, template: TemplateRecord) -> FileInfo:
        return cls(
            template_id=template.id,
            template_title=template.title,
            filename=template.main_file,
            timestamp=datetime.now().isoformat(),
        )


@dataclass
class DownloadMainFilesWorkerObject(StandardAdminWorkerObject):
    output_path: str | None = None
    files_downloaded: list[dict[str, Any]] = field(default_factory=list)
    files_failed: list[dict[str, Any]] = field(default_factory=list)
    files_processed: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "DownloadMainFilesWorkerObject",
    "FileInfo",
]
