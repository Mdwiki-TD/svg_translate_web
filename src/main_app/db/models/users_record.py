from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ...core.crypto import decrypt_value

logger = logging.getLogger(__name__)


@dataclass
class AdminUserRecord:
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


@dataclass
class UserTokenRecord:
    """Decrypted OAuth credential bundle stored in the database."""

    user_id: int
    username: str
    access_token: bytes
    access_secret: bytes
    created_at: Any | None = None
    updated_at: Any | None = None
    last_used_at: Any | None = None
    rotated_at: Any | None = None

    def decrypted(self) -> tuple[str, str]:
        """Return the decrypted access token and secret."""

        access_key = decrypt_value(self.access_token)
        access_secret = decrypt_value(self.access_secret)
        # mark_token_used(self.user_id)
        return access_key, access_secret
