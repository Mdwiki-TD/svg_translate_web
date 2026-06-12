"""
Objects for collect_templates_data worker.

    "note": "",
    "status": "pending",
    "errors": [],
    "args": {},
    "job_id": self.job_id,
    "started_at": datetime.now().isoformat(),
    "completed_at": None,
    "cancelled_at": None,
    "summary": {
        "total": 0,
        "processed": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
    },
    "pages_processed": [],
    "pages_added": [],
    "pages_updated": [],
    "pages_skipped": [],
    "pages_failed": [],
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class TemplateInfo:
    """
    Holds all state for a single template being processed.
    """

    id: int
    title: str
    new_main_file: str
    last_world_file: str
    source: str
    status: str = "processing"
    error: str | None = None
    error_type: str | None = None
    steps: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "main_file": {"result": None, "value": "", "new_value": "", "msg": ""},
            "last_world_file": {"result": None, "value": "", "new_value": "", "msg": ""},
            "source": {"result": None, "value": "", "new_value": "", "msg": ""},
            "slug": {"result": None, "value": "", "new_value": "", "msg": ""},
        }
    )

    def to_dict(self) -> dict[str, Any]:
        """
        convert to dict.
        """
        return asdict(self)



@dataclass
class CollectTemplatesDataWorkerObject(StandardAdminWorkerObject):
    pages_added: list[dict[str, Any]] = field(default_factory=list)
    pages_updated: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "CollectTemplatesDataWorkerObject",
]
