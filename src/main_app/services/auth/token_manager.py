"""
TokenManager — full lifecycle management for encrypted OAuth tokens.
"""

from __future__ import annotations

import logging

from ...database.services import (
    AdminService,
    UsersService,
    UserTokenService,
)
from ..core.crypto import CryptoService
from .current_user import CurrentUser, UserTokenRecord

logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(self) -> None:
        self.users_service = UsersService()
        self.user_token_service = UserTokenService()
        self.admin_service = AdminService()
        self._crypto = CryptoService()

    def save_token(
        self,
        user_id: int,
        access_token: str,
        access_secret: str,
    ) -> UserTokenRecord | None:
        """
        Encrypt plaintext tokens and persist them for ``user_id``.
        """
        try:
            encrypted_token = self._crypto.encrypt(access_token)
            encrypted_secret = self._crypto.encrypt(access_secret)

            # 1. Update or insert into database via repository
            return self.user_token_service.upsert_user_token(
                user_id=user_id,
                encrypted_token=encrypted_token,
                encrypted_secret=encrypted_secret,
            )

        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

    def get_authenticated_user(self, user_id: int) -> CurrentUser | None:
        """Fetch the CurrentUser composite for session restoration."""
        try:
            token = self.user_token_service.get_authenticated_user_token(user_id)
            if not token:
                return None

            return CurrentUser.from_authenticated(
                token=token,
                is_active_admin=self.admin_service.is_active_coordinator(token.user.username),
            )
        except Exception as e:
            logger.error("Error loading user for ID %s: %s", user_id, e)
            return None

    def get_decrypted_token(self, user_id: int) -> dict | None:
        """
        Load encrypted tokens for ``user_id`` and return decrypted values.
        """
        record = self.user_token_service.get_record_by_id(user_id)
        if record is None:
            return None
        return {
            "access_token": self._crypto.decrypt(record.access_token),
            "access_secret": self._crypto.decrypt(record.access_secret),
        }

    def touch(self, user_id: int) -> None:
        """Update last_used_at timestamp for ``user_id``."""
        self.user_token_service.update_last_used(user_id)

    def delete_token(self, user_id: int) -> bool:
        """Delete the user's stored token (logout / revoke)."""
        return self.user_token_service.delete(user_id)

    def has_token(self, user_id: int) -> bool:
        """Check whether a token exists for this user."""
        return self.user_token_service.get_record_by_id(user_id) is not None


__all__ = [
    "TokenManager",
]
