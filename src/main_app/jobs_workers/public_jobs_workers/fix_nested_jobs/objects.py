"""
Objects for fix_nested_jobs worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...base_worker import WorkerMapping


@dataclass
class StageDetail:
    name: str = ""
    status: str = "pending"
    message: str = ""

    def _update(self, status: str, message: str) -> None:
        if status:
            self.status = status
        if message:
            self.message = message


@dataclass
class Stages:
    download: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="download",
            message="Downloading files",
        )
    )
    analyze: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="analyze",
            message="Analyzing nested tags",
        )
    )
    fix: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="fix",
            message="Fixing nested tags",
        )
    )
    verify: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="verify",
            message="Verifying fixes",
        )
    )
    upload: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="upload",
            message="Uploading fixed files",
        )
    )


@dataclass
class FileResult:
    status: str = "pending"
    path: str | None = None
    error: str | None = None
    success: bool | None = None
    nested_tags_before: int = 0
    nested_tags: list[str] = field(default_factory=list)
    nested_tags_after: int = 0
    nested_tags_fixed: int = 0


@dataclass
class FixNestedJobsWorkerObject(WorkerMapping):
    job_id: int | None = None
    note: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    filename: str | None = None
    file_result: FileResult = field(default_factory=FileResult)
    stages: Stages = field(default_factory=Stages)


__all__ = [
    "FixNestedJobsWorkerObject",
    "StageDetail",
    "Stages",
    "FileResult",
]
