"""
Objects for add_svglanguages_template worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from ...shared_objects import STATUS_LITERAL, StandardAdminWorkerObject


@dataclass
class OneStep:
    result: bool | None = None
    msg: str | None = None
    newrevid: int = 0


@dataclass
class InfoSteps:
    load_template_text: OneStep = field(default_factory=OneStep)
    generate_template_text: OneStep = field(default_factory=OneStep)
    add_template_text: OneStep = field(default_factory=OneStep)
    save_new_text: OneStep = field(default_factory=OneStep)

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like access for backward compatibility with templates."""
        return getattr(self, key, default)


@dataclass
class TemplateInfo:
    """Holds all state for a single template being processed."""

    template_id: int
    template_title: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: STATUS_LITERAL = "pending"
    error: str | None = None
    steps: InfoSteps = field(default_factory=InfoSteps)

    # Internal temporary state
    _text: str | None = None
    _template_text: str | None = None
    _new_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "timestamp": self.timestamp,
            "status": self.status,
            "error": self.error,
            "steps": asdict(self.steps),
        }


@dataclass
class AddSvgLanguagesWorkerObject(StandardAdminWorkerObject):
    pass


__all__ = [
    "AddSvgLanguagesWorkerObject",
]
