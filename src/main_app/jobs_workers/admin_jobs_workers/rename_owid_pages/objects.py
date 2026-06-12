"""Objects for rename_owid_pages worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class RenameOwidPagesSummary:
    total: int = 0
    processed: int = 0
    checked: int = 0
    renamed: int = 0
    skipped_target_exists: int = 0
    redirected: int = 0
    failed: int = 0


@dataclass
class RenameOwidPagesWorkerObject(StandardAdminWorkerObject):
    summary: RenameOwidPagesSummary = field(default_factory=RenameOwidPagesSummary)


__all__ = [
    "RenameOwidPagesWorkerObject",
    "RenameOwidPagesSummary",
]
