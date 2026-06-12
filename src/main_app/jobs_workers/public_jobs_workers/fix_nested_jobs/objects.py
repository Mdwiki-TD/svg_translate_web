"""Objects for fix_nested_jobs worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from ...base_worker_object import WorkerObject


@dataclass
class StageDetail:
    status: str = "Pending"
    message: str = ""


@dataclass
class Stages:
    download: StageDetail = field(default_factory=lambda: StageDetail(message="Downloading files"))
    analyze: StageDetail = field(default_factory=lambda: StageDetail(message="Analyzing nested tags"))
    fix: StageDetail = field(default_factory=lambda: StageDetail(message="Fixing nested tags"))
    verify: StageDetail = field(default_factory=lambda: StageDetail(message="Verifying fixes"))
    upload: StageDetail = field(default_factory=lambda: StageDetail(message="Uploading fixed files"))


@dataclass
class FileResult:
    status: str = "pending"
    path: Optional[str] = None
    error: Optional[str] = None
    success: Optional[bool] = None
    nested_tags_before: int = 0
    nested_tags: list[str] = field(default_factory=list)
    nested_tags_after: int = 0
    nested_tags_fixed: int = 0


@dataclass
class FixNestedJobsWorkerObject(WorkerObject):
    job_id: Optional[int] = None
    note: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    filename: Optional[str] = None
    file_result: FileResult = field(default_factory=FileResult)
    stages: Stages = field(default_factory=Stages)


__all__ = [
    "FixNestedJobsWorkerObject",
    "StageDetail",
    "Stages",
    "FileResult",
]
