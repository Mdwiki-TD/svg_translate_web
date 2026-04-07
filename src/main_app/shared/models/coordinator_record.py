from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CoordinatorRecord:
    """Representation of a coordinator/admin account."""

    id: int
    username: str
    is_active: bool
    created_at: Any | None = None
    updated_at: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the record to a dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
