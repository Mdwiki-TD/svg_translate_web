"""
Objects for create_owid_pages worker.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ....database.models import TemplateRecord
from ....jobs.shared_objects import STATUS_LITERAL, OneStep, SharedMapToJson, SharedworkerObject


@dataclass
class InfoSteps:
    load_template_text: OneStep = field(default_factory=OneStep)
    create_new_text: OneStep = field(default_factory=OneStep)
    update_text: OneStep = field(default_factory=OneStep)
    create_new_page: OneStep = field(default_factory=OneStep)


@dataclass
class TemplateProcessingInfo(SharedMapToJson):
    """Holds all state for a single template being processed."""

    template_id: int
    template_title: str
    status: STATUS_LITERAL = "pending"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    steps: InfoSteps = field(default_factory=InfoSteps)

    # Internal temporary state
    _template_text: str | None = None
    _new_text: str | None = None

    error: str | None = None

    new_page_title: str | None = None
    slug: str | None = None

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
class CreateOwidPagesWorkerObject(SharedworkerObject):
    summary: CreateOwidPagesSummary = field(default_factory=CreateOwidPagesSummary)
    pages_created: list[TemplateProcessingInfo] = field(default_factory=list)
    pages_updated: list[TemplateProcessingInfo] = field(default_factory=list)


__all__ = [
    "CreateOwidPagesWorkerObject",
    "CreateOwidPagesSummary",
]
