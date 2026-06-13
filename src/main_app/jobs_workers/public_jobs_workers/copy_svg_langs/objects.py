"""
Objects for copy_svg_langs worker.
{
    "note": "",
    "status": "pending",
    "errors": [],
    "args": {},
    "job_id": "self.job_id",
    "started_at": "datetime.now().isoformat()",
    "completed_at": None,
    "cancelled_at": None,
    "summary": {},
    "title": None,
    "stages": {
        "text": {"status": "Pending", "message": "Getting text"},
        "titles": {"status": "Pending", "message": "Getting titles"},
        "translations": {"status": "Pending", "message": "Getting translations"},
        "download": {"status": "Pending", "message": "Downloading files"},
        "nested": {"status": "Pending", "message": "Analyze nested files"},
        "inject": {"status": "Pending", "message": "Injecting translations"},
        "upload": {"status": "Pending", "message": "Uploading files"},
    },
    "results_summary": {},
    "files_processed": {},
}
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class StageDetail:
    name: str = ""
    status: str = "Pending"
    message: str = ""
    data: Any = None


@dataclass
class Stages:
    text: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="text",
            message="Getting text",
        )
    )
    titles: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="titles",
            message="Getting titles",
        )
    )
    translations: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="translations",
            message="Getting translations",
        )
    )
    download: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="download",
            message="Downloading files",
        )
    )
    nested: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="nested",
            message="Analyze nested files",
        )
    )
    inject: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="inject",
            message="Injecting translations",
        )
    )
    upload: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="upload",
            message="Uploading files",
        )
    )


@dataclass
class StepResult:
    result: Optional[bool] = None
    msg: str = ""


@dataclass
class FileSteps:
    download: StepResult = field(default_factory=lambda: StepResult())
    nested: StepResult = field(default_factory=lambda: StepResult())
    inject: StepResult = field(default_factory=lambda: StepResult())
    upload: StepResult = field(default_factory=lambda: StepResult())


@dataclass
class FilesProcessedItem:
    title: str
    status: str = "pending"
    error: Optional[str] = None
    steps: FileSteps = field(default_factory=lambda: FileSteps())


@dataclass
class CopySvgLangsWorkerObject(StandardAdminWorkerObject):
    job_id: Optional[int] = None
    note: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    stages: Stages = field(default_factory=Stages)
    results_summary: dict[str, Any] = field(default_factory=dict)
    files_processed: dict[str, FilesProcessedItem] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """

        return asdict(self)


__all__ = [
    "StageDetail",
    "Stages",
    "StepResult",
    "FileSteps",
    "FilesProcessedItem",
    "CopySvgLangsWorkerObject",
]
