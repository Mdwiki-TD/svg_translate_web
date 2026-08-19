"""
Objects for create_owid_pages worker.

"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal

from ....database.models import TemplateRecord
from ...shared_objects import StandardAdminWorkerObject

STATUS_LIST = Literal["pending", "completed", "skipped", "updated", "created", "failed"]


@dataclass
class OneStep:
    result: bool | None = None
    msg: str | None = None
    newrevid: int = 0


@dataclass
class InfoSteps:
    load_template_text: OneStep = field(default_factory=OneStep)
    create_new_text: OneStep = field(default_factory=OneStep)
    update_text: OneStep = field(default_factory=OneStep)
    create_new_page: OneStep = field(default_factory=OneStep)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for backward compatibility with templates."""
        return getattr(self, key, default)


@dataclass
class TemplateProcessingInfo:
    """Holds all state for a single template being processed."""

    template_id: int
    template_title: str
    new_page_title: str | None = None
    slug: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: STATUS_LIST = "pending"
    error: str | None = None
    steps: InfoSteps = field(default_factory=InfoSteps)

    # Internal temporary state
    _template_text: str | None = None
    _new_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "new_page_title": self.new_page_title,
            "slug": self.slug,
            "timestamp": self.timestamp,
            "status": self.status,
            "error": self.error,
            "steps": asdict(self.steps),
        }

    @classmethod
    def from_template(cls, template: TemplateRecord) -> TemplateProcessingInfo:
        return cls(
            template_id=template.id,
            template_title=template.title,
            slug=template.slug,
        )


@dataclass
class CreateOwidPagesSummary:
    total: int = 0
    processed: int = 0
    created: int = 0
    updated: int = 0
    failed: int = 0
    skipped: int = 0


@dataclass
class CreateOwidPagesWorkerObject(StandardAdminWorkerObject):
    summary: CreateOwidPagesSummary = field(default_factory=CreateOwidPagesSummary)
    pages_created: list[dict[str, Any]] = field(default_factory=list)
    pages_updated: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "CreateOwidPagesWorkerObject",
    "CreateOwidPagesSummary",
]
