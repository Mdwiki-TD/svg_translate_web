"""
Objects for collect_templates_data worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ...shared_objects import StandardAdminSummary, WorkerObject


@dataclass
class StepResult:
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


@dataclass
class FileSteps:
    main_file: StepResult = field(default_factory=lambda: StepResult())
    last_world_file: StepResult = field(default_factory=lambda: StepResult())
    newest_year: StepResult = field(default_factory=lambda: StepResult())
    source: StepResult = field(default_factory=lambda: StepResult())
    slug: StepResult = field(default_factory=lambda: StepResult())
    files: StepResult = field(default_factory=lambda: StepResult())

    @classmethod
    def from_template(cls, template: TemplateData) -> TemplateInfos:
        return cls(
            main_file=StepResult(value=template.main_file or ""),
            last_world_file=StepResult(value=template.last_world_file or ""),
            source=StepResult(value=template.source),
            slug=StepResult(value=template.slug),
        )


@dataclass
class TemplateInfos:
    """
    Holds all state for a single template being processed.
    """

    id: int
    title: str
    source: str
    status: Literal["processing", "skipped", "updated", "failed", "completed"] = "processing"
    steps: FileSteps = field(default_factory=lambda: FileSteps())

    error: str | None = None
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]

    @classmethod
    def from_template(cls, template: TemplateData) -> TemplateInfos:
        return cls(
            id=template.id,
            title=template.title,
            source="",
            status="",
            steps=FileSteps.from_template(template),
        )


@dataclass
class TemplateData:
    id: int = 0
    title: str = ""
    main_file: str | None = None
    last_world_file: str | None = None
    last_world_year: int | None = None
    slug: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        if self.main_file:
            self.main_file = self.main_file.removeprefix("File:")
        if self.last_world_file:
            self.last_world_file = self.last_world_file.removeprefix("File:")


@dataclass
class CollectTemplatesDataWorkerObject(WorkerObject):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    pages_added: list[TemplateInfos] = field(default_factory=list)
    pages_updated: list[TemplateInfos] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)
    pages_failed: list[dict[str, Any]] = field(default_factory=list)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    args: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "CollectTemplatesDataWorkerObject",
]
