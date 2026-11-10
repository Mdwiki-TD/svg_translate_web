"""
Objects for update_wikitext worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ...shared_objects import OneStep, StandardAdminSummary, WorkerMapping

STATUS_LIST = Literal["completed", "failed", "pending", "skipped", "success"]


@dataclass
class InfoSteps:
    load_text: OneStep = field(default_factory=OneStep)
    update_text: OneStep = field(default_factory=OneStep)
    save_page: OneStep = field(default_factory=OneStep)


@dataclass
class ProcessingFileInfo:
    """Holds all state for a single template being processed."""

    title: str
    status: STATUS_LIST = "pending"
    error: str | None = None
    steps: InfoSteps = field(default_factory=lambda: InfoSteps())


@dataclass
class UpdateFilesWikiTextObject(WorkerMapping):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    title: str | None = None

    files_success: list[ProcessingFileInfo] = field(default_factory=list)
    files_skipped: list[ProcessingFileInfo] = field(default_factory=list)
    files_failed: list[ProcessingFileInfo] = field(default_factory=list)
    files_processed: list[ProcessingFileInfo] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        """Converts the dataclass instance back to its original dictionary format."""
        return asdict(self)

    def update_status(self, info: ProcessingFileInfo) -> None:
        """ """
        self.summary.processed += 1

        if info.status in ["pending", "running"]:
            info.status = "completed"

        if info.status == "skipped":
            self.files_skipped.append(info)

        elif info.status == "failed":
            self.files_failed.append(info)

        elif info.status == "success":
            self.files_success.append(info)

        else:
            self.files_processed.append(info)


__all__ = [
    "UpdateFilesWikiTextObject",
]
