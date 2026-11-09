"""
Objects for create_owid_pages worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ...shared_objects import STATUS_LITERAL, OneStep, WorkerMapping, StandardAdminSummary


@dataclass
class InfoSteps:
    load_template_text: OneStep = field(default_factory=OneStep)
    create_new_text: OneStep = field(default_factory=OneStep)
    update_text: OneStep = field(default_factory=OneStep)
    create_new_page: OneStep = field(default_factory=OneStep)


@dataclass
class ProcessingFileInfo:
    """Holds all state for a single template being processed."""

    title: str
    status: STATUS_LITERAL = "pending"
    error: str | None = None
    steps: InfoSteps = field(default_factory=lambda: InfoSteps())

    wikitext: str | None = None
    new_wikitext: str | None = None

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("wikitext", None)
        data.pop("new_wikitext", None)
        return data


@dataclass
class UpdateFilesWikiTextObject(WorkerMapping):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    title: str | None = None

    files_processed: list[ProcessingFileInfo] = field(default_factory=list)
    files_success: list[ProcessingFileInfo] = field(default_factory=list)
    files_skipped: list[ProcessingFileInfo] = field(default_factory=list)
    files_failed: list[ProcessingFileInfo] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        """Converts the dataclass instance back to its original dictionary format."""
        return asdict(self)


__all__ = [
    "UpdateFilesWikiTextObject",
]
