"""
Objects for rename_owid_pages worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from ....jobs.shared_objects import SharedMapToJson, SharedworkerObject

STATUS_LIST3 = Literal[
    "failed",
    "pending",
    "redirected",
    "renamed",
    "skipped_target_exists",
]


@dataclass
class RenameInfo(SharedMapToJson):
    """Holds the outcome of attempting to rename a single page."""

    namespace: int
    old_title: str
    new_title: str | None = None
    newrevid: int | None = None
    status: STATUS_LIST3 = "pending"
    full_prefix: str = ""
    msg: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def make_new_title(self) -> str:
        if not self.old_title.startswith(self.full_prefix):
            return self.old_title

        rest = self.old_title[len(self.full_prefix) :]
        if not rest:
            return self.old_title

        first = rest[0]

        if first.isalpha() and first.islower():
            return self.full_prefix + first.upper() + rest[1:]

        return self.old_title

    def needs_rename(self) -> bool:
        """
        Decide whether *title* needs a rename.

        Only the first character after ``full_prefix`` is changed; everything
        else (including spaces / underscores) is preserved as-is.
        """
        new = self.make_new_title()

        if new != self.old_title:
            self.new_title = new
            return True

        return False


@dataclass
class RenameOwidPagesSummary(SharedMapToJson):
    total: int = 0
    processed: int = 0
    checked: int = 0
    renamed: int = 0
    skipped_target_exists: int = 0
    redirected: int = 0
    failed: int = 0


@dataclass
class RenameOwidPagesWorkerObject(SharedworkerObject):
    summary: RenameOwidPagesSummary = field(default_factory=RenameOwidPagesSummary)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    pages_renamed: list[dict[str, Any]] = field(default_factory=list)
    pages_redirected: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "RenameOwidPagesWorkerObject",
    "RenameOwidPagesSummary",
]
