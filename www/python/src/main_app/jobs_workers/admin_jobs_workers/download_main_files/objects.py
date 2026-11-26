"""
Objects for download_main_files worker.


"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from ....database.models import TemplateRecord
from ....jobs.shared_objects import SharedMapToJson, SharedworkerObject

STATUS = Literal[
    "pending",
    "running",
    "completed",
    "downloaded",
    "failed",
]


@dataclass
class FileInfo(SharedMapToJson):
    template_id: int
    template_title: str
    filename: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: STATUS = "pending"
    error: None | str = None
    error_type: None | str = None
    path: None | str = None
    size_bytes: None | int = None

    @classmethod
    def from_template(cls, template: TemplateRecord) -> FileInfo:
        return cls(
            template_id=template.id,
            template_title=template.title,
            filename=template.main_file,  # pyright: ignore[reportArgumentType]
            timestamp=datetime.now().isoformat(),
        )


@dataclass
class DownloadMainFilesWorkerObject(SharedworkerObject):
    output_path: str | None = None
    files_downloaded: list[FileInfo] = field(default_factory=list)
    files_failed: list[FileInfo] = field(default_factory=list)
    files_processed: list[FileInfo] = field(default_factory=list)


__all__ = [
    "DownloadMainFilesWorkerObject",
    "FileInfo",
]
