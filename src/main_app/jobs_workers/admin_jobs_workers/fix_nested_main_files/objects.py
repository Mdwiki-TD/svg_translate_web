"""
Objects for fix_nested_main_files worker.

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
            "pages_success": [],
            "pages_skipped": [],
            "pages_failed": [],
            """

from __future__ import annotations

from dataclasses import dataclass

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class FixNestedMainFilesWorkerObject(StandardAdminWorkerObject):
    pass


__all__ = [
    "FixNestedMainFilesWorkerObject",
]
