"""
Objects for update_wikitext worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ...shared_objects import OneItem, OneStep, StandardAdminSummary, WorkerMapping

STATUS_LITERAL = Literal["completed", "failed", "pending", "skipped", "updated"]


@dataclass
class InfoSteps:
    load_text: OneStep = field(default_factory=OneStep)
    update_author: OneStep = field(default_factory=OneStep)
    update_langs: OneStep = field(default_factory=OneStep)
    save_page: OneStep = field(default_factory=OneStep)


@dataclass
class ProcessingFileInfo(OneItem):
    """Holds all state for a single template being processed."""

    error: str | None = None
    langs: list[str] = field(default_factory=list)
    steps: InfoSteps = field(default_factory=lambda: InfoSteps())

    def create_summary_message(self, author_citation: str) -> str:
        summary = []
        if self.steps.update_author.result:
            summary.append(f"Updated author to {author_citation}")

        if self.steps.update_langs.result:
            row = ",".join(self.langs)
            summary.append(f"Insert Svg lang ({row})")

        return ", ".join(summary)


@dataclass
class UpdateFilesWikiTextObject(WorkerMapping):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    title: str | None = None

    files_updated: list[ProcessingFileInfo] = field(default_factory=list)
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

        elif info.status == "updated":
            self.files_updated.append(info)

        else:
            self.files_processed.append(info)


__all__ = [
    "UpdateFilesWikiTextObject",
]
