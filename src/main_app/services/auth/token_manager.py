"""User authentication service — bridges OAuth callbacks to the DB layer."""

from __future__ import annotations

import logging

from ...database.models import UserRecord
from ...database.services import (
    AdminService,
    UsersService,
    UserTokenService,
)
from ..core.crypto import CryptoService
from .current_user import CurrentUser

logger = logging.getLogger(__name__)


class TokenManager:
    def __init__(self) -> None:
        self.users_service = UsersService()
        self.user_token_service = UserTokenService()
        self.admin_service = AdminService()
        self._crypto = CryptoService()

    def save_token(
        self,
        username: str,
        access_token: str,
        access_secret: str,
    ) -> CurrentUser | None:
        """Upsert OAuth credentials and return a CurrentUser composite."""
        username = (username or "").strip()
        if not username:
            logger.warning("OAuth callback received an empty username")
            return None

        try:
            # Ensure user identity row exists
            user: UserRecord | None = self.users_service.get_user_by_username(username)

            if not user:
                user: UserRecord | None = self.users_service.create_user(username)

            if not user:
                return None

        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        try:
            encrypted_token = self._crypto.encrypt(access_token)
            encrypted_secret = self._crypto.encrypt(access_secret)

            # 1. Update or insert into database via repository
            self.user_token_service.upsert_user_token(
                user_id=user.user_id,
                encrypted_token=encrypted_token,
                encrypted_secret=encrypted_secret,
            )

        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        try:
            # 2. Get the fresh record
            token = self.user_token_service.get_user_token(user.user_id)
            if not token:
                return None

            is_active_admin = self.admin_service.is_active_coordinator(username)
        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        return CurrentUser.from_authenticated(
            token=token,
            is_active_admin=is_active_admin,
        )

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


__all__ = [
    "TokenManager",
]
