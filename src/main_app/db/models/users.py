from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ...core.crypto import decrypt_value

logger = logging.getLogger(__name__)


@dataclass
class AdminUserRecord:
    """
    CREATE TABLE `admin_users` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `username` varchar(255) NOT NULL,
      `is_active` tinyint(1) NOT NULL DEFAULT 1,
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `username` (`username`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "admin_users"

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


__all__ = [
    "UserTokenRecord",
    "AdminUserRecord",
]
