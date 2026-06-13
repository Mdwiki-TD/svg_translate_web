"""
Objects for fix_nested_main_files worker.

"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class TemplateInfo:
    id: int
    title: str
    main_file: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = ""
    reason: None | str = None
    fix_result: None | dict = None
    error_type: None | str = None

    def to_dict(self) -> dict[str, Any]:
        """
        convert to dict.
        """
        return asdict(self)


@dataclass
class FixNestedMainFilesWorkerObject(StandardAdminWorkerObject):
    pass


_old_result = {
    "note": "",
    "status": "pending",
    "errors": [],
    "args": {},
    "job_id": "self.job_id",
    "started_at": "datetime.now().isoformat()",
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
    "pages_success": [],
    "pages_skipped": [],
    "pages_failed": [],
}
__all__ = [
    "FixNestedMainFilesWorkerObject",
    "TemplateInfo",
]
