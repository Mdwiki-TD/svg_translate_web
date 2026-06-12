"""Objects for collect_templates_data worker."""

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
