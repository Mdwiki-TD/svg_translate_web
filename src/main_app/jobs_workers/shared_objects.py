""" """

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: Literal["missing", "changed", "error", "skipped"]
    newrevid: int = 0
    msg: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Summary:
    scanned: int = 0
    total: int = 0


@dataclass
class SharedworkerObject(WorkerObject):
    summary: Summary = field(default_factory=Summary)

    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    pages_changed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)

    pages_missing: list[str] = field(default_factory=list)
    note: str = ""


__all__ = [
    "Summary",
    "SharedworkerObject",
    "UpdaterOutcome",
]
