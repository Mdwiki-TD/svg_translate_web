"""
Objects for collect_templates_data worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ....database.models import TemplateRecord
from ...shared_objects import STATUS_LIST, StandardAdminSummary, WorkerMapping


@dataclass
class CollectStepResult:
    """
    "main_file": {"result": None, "value": "", "new_value": "", "msg": ""},
    """

    result: bool | str | None = None
    value: str = ""
    new_value: str = ""
    msg: str = ""

    def _update(self, result: str = "", msg: str = "", new_value: str = "") -> None:
        if result:
            self.result = result

        if msg:
            self.msg = msg

        if new_value:
            self.new_value = new_value

    def _update_if_diff(self, new_value: str | None = "") -> None:
        if not new_value:
            return

        if self.value != new_value:
            self.new_value = new_value
            self.result = "updated"
        else:
            self.result = "skipped"
            self.msg = "No changes"


@dataclass
class CollectFileSteps:
    main_file: CollectStepResult = field(default_factory=lambda: CollectStepResult())
    last_world_file: CollectStepResult = field(default_factory=lambda: CollectStepResult())
    newest_year: CollectStepResult = field(default_factory=lambda: CollectStepResult())
    source: CollectStepResult = field(default_factory=lambda: CollectStepResult())
    slug: CollectStepResult = field(default_factory=lambda: CollectStepResult())
    files: CollectStepResult = field(default_factory=lambda: CollectStepResult())

    @classmethod
    def from_template(cls, template: TemplateData) -> CollectFileSteps:
        return cls(
            main_file=CollectStepResult(value=template.main_file or ""),
            last_world_file=CollectStepResult(value=template.last_world_file or ""),
            newest_year=CollectStepResult(value=str(template.last_world_year or "")),
            source=CollectStepResult(value=template.source),
            slug=CollectStepResult(value=template.slug),
            files=CollectStepResult(value=str(template.files or "")),
        )


@dataclass
class TemplateInfos:
    """
    Holds all state for a single template being processed.
    """

    id: int
    title: str
    source: str
    status: STATUS_LIST = "pending"
    steps: CollectFileSteps = field(default_factory=lambda: CollectFileSteps())

    error: str | None = None
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_template(cls, template: TemplateData) -> TemplateInfos:
        return cls(
            id=template.id,
            title=template.title,
            source="",
            status="pending",
            steps=CollectFileSteps.from_template(template),
        )


@dataclass
class TemplateData:
    id: int = 0
    title: str = ""
    main_file: str | None = None
    last_world_file: str | None = None
    last_world_year: int | None = None
    files: int | None = None
    slug: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        if self.main_file:
            self.main_file = self.main_file.removeprefix("File:")
        if self.last_world_file:
            self.last_world_file = self.last_world_file.removeprefix("File:")

    @classmethod
    def from_template(cls, x: TemplateRecord) -> TemplateData:
        return cls(
            id=x.id,
            title=x.title,
            main_file=x.main_file,
            last_world_file=x.last_world_file,
            last_world_year=x.last_world_year,
            files=x.files,
            slug=x.slug,
            source=x.source,
        )


@dataclass
class CollectTemplatesDataMapping(WorkerMapping):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    pages_added: list[TemplateInfos] = field(default_factory=list)
    pages_updated: list[TemplateInfos] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)
    pages_failed: list[dict[str, Any]] = field(default_factory=list)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    args: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "CollectTemplatesDataMapping",
]
