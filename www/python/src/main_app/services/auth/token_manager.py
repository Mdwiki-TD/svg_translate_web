"""
TokenManager — full lifecycle management for encrypted OAuth tokens.
"""

from __future__ import annotations

import logging

from ...database.services import (
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
            token, is_active = self.user_token_service.get_authenticated_user_context(user_id)
            if not token:
                return None

            return CurrentUser.from_authenticated(
                token=token,
                is_active_admin=is_active,
            )
        except Exception as e:
            logger.error("Error loading user for ID %s: %s", user_id, e)
            return None

    def get_auth_payload_by_username(self, username: str) -> dict | None:
        """Rebuild the execution identity of a user from their username.

        Used to start queued jobs long after the request that submitted them
        ended. Only the username is persisted with the job; the (encrypted)
        OAuth credentials are loaded again here, so no secret ever lives in
        the queue payload.

        Args:
            username: The job owner's username.

        Returns:
            A mapping with ``id``, ``username``, ``access_token`` and
            ``access_secret`` (still encrypted), or None when the user has no
            stored credentials.
        """
        if not username:
            return None

        try:
            token = self.user_token_service.get_user_token_by_username(username)
        except Exception:
            logger.exception("Failed to load credentials by username")
            return None

        if token is None:
            return None

        return {
            "id": token.user_id,
            "username": username,
            "access_token": token.access_token,
            "access_secret": token.access_secret,
        }

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
