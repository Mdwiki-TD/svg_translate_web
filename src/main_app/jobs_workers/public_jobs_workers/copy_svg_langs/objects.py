"""
Objects for copy_svg_langs worker.

            "note": "",
            "status": "pending",
            "errors": [],
            "args": {},
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
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
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ...base_worker_object import WorkerObject


@dataclass
class StageDetail:
    status: str = "Pending"
    message: str = ""
    data: Any = None


@dataclass
class Stages:
    text: StageDetail = field(default_factory=lambda: StageDetail(message="Getting text"))
    titles: StageDetail = field(default_factory=lambda: StageDetail(message="Getting titles"))
    translations: StageDetail = field(default_factory=lambda: StageDetail(message="Getting translations"))
    download: StageDetail = field(default_factory=lambda: StageDetail(message="Downloading files"))
    nested: StageDetail = field(default_factory=lambda: StageDetail(message="Analyze nested files"))
    inject: StageDetail = field(default_factory=lambda: StageDetail(message="Injecting translations"))
    upload: StageDetail = field(default_factory=lambda: StageDetail(message="Uploading files"))


@dataclass
class StepResult:
    result: Optional[bool] = None
    msg: str = ""


@dataclass
class FilesProcessedItem:
    title: str
    status: str = "pending"
    error: Optional[str] = None
    steps: dict[str, Any] = field(
        default_factory=lambda: {
            "download": {"result": None, "msg": ""},
            "nested": {"result": None, "msg": ""},
            "inject": {"result": None, "msg": ""},
            "upload": {"result": None, "msg": ""},
        }
    )


@dataclass
class CopySvgLangsWorkerObject(WorkerObject):
    job_id: Optional[int] = None
    note: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    stages: Stages = field(default_factory=Stages)
    results_summary: dict[str, Any] = field(default_factory=dict)
    files_processed: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "CopySvgLangsWorkerObject",
    "StageDetail",
    "Stages",
    "FilesProcessedItem",
]
