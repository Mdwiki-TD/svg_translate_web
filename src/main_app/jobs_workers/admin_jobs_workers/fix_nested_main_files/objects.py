"""Objects for fix_nested_main_files worker."""

from __future__ import annotations

from dataclasses import dataclass

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class FixNestedMainFilesWorkerObject(StandardAdminWorkerObject):
    pass


__all__ = [
    "FixNestedMainFilesWorkerObject",
]
