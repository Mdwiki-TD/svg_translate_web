""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ...base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


@dataclass
class RedirectsSummary:
    scanned: int = 0
    total: int = 0

    created: int = 0
    errors: int = 0
    skipped: int = 0

    already_exists: int = 0
    target_missing: int = 0


@dataclass
class CreateRedirectsWorkerObject(WorkerObject):
    summary: RedirectsSummary = field(default_factory=RedirectsSummary)
    pages_to_work: list[str] = field(default_factory=list)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "RedirectsSummary",
    "CreateRedirectsWorkerObject",
]
