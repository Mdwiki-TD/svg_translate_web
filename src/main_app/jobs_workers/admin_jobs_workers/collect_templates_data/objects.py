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

from dataclasses import dataclass, field
from typing import Any

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class CollectTemplatesDataWorkerObject(StandardAdminWorkerObject):
    pages_added: list[dict[str, Any]] = field(default_factory=list)
    pages_updated: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "CollectTemplatesDataWorkerObject",
]
