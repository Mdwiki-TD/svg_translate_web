"""
Objects for add_svglanguages_template worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ...shared_objects import StandardAdminWorkerObject, STATUS_LITERAL


@dataclass
class TemplateInfo:
    """Holds all state for a single template being processed."""

    template_id: int
    template_title: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: STATUS_LITERAL = "pending"
    error: str | None = None
    steps: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "load_template_text": {"result": None, "msg": ""},
            "generate_template_text": {"result": None, "msg": ""},
            "add_template_text": {"result": None, "msg": ""},
            "save_new_text": {"result": None, "msg": ""},
        }
    )

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
            "steps": self.steps,
        }


@dataclass
class AddSvgLanguagesWorkerObject(StandardAdminWorkerObject):
    pass


__all__ = [
    "AddSvgLanguagesWorkerObject",
]
