"""User authentication service — bridges OAuth callbacks to the DB layer."""

from __future__ import annotations

import logging
from typing import Optional

from ...db.services import (
    create_user,
    get_authenticated_user_token,
    get_user_by_username,
    get_user_token,
    is_active_coordinator,
    upsert_user_token,
)
from ...db.services.users_service import UserRecord
from .current_user import CurrentUser

logger = logging.getLogger(__name__)


class AuthUserService:
    @staticmethod
    def save_and_get_user(
        username: str,
        access_key: str,
        access_secret: str,
    ) -> Optional[CurrentUser]:
        """Upsert OAuth credentials and return a CurrentUser composite."""
        username = (username or "").strip()
        if not username:
            logger.warning("OAuth callback received an empty username")
            return None

        try:
            # Ensure user identity row exists
            user: Optional[UserRecord] = get_user_by_username(username)

            if not user:
                user: Optional[UserRecord] = create_user(username)

            if not user:
                return None

            user_id: int = user.user_id

        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        try:
            # 1. Update or insert into database via repository
            upsert_user_token(
                user_id=user_id,
                access_key=access_key,
                access_secret=access_secret,
            )

        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        try:
            # 2. Get the fresh record
            token = get_user_token(user_id)
            if not token:
                return None

            is_active_admin = is_active_coordinator(username)
        except Exception as e:
            logger.exception("Failed to upsert or fetch user credentials: %s", e)
            return None

        return CurrentUser(
            user_id=user_id,
            username=username,
            access_token=token.access_token,
            access_secret=token.access_secret,
            is_active_admin=is_active_admin,
            can_run_jobs=user.can_run_jobs,
            can_run_bg_jobs=user.can_run_bg_jobs,
        )

    @staticmethod
    def get_authenticated_user(user_id: int) -> Optional[CurrentUser]:
        """Fetch the CurrentUser composite for session restoration."""
        try:
            token = get_authenticated_user_token(user_id)
            if not token:
                return None
            username = token.user.username
            return CurrentUser(
                user_id=user_id,
                username=username,
                access_token=token.access_token,
                access_secret=token.access_secret,
                is_active_admin=is_active_coordinator(username),
                can_run_jobs=token.user.can_run_jobs,
                can_run_bg_jobs=token.user.can_run_bg_jobs,
            )
        except Exception as e:
            logger.error("Error loading user for ID %s: %s", user_id, e)
            return None


__all__ = [
    "AuthUserService",
]
