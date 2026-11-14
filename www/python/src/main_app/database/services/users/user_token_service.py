"""
SQLAlchemy-based service for managing user tokens.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import exists
from sqlalchemy.orm import contains_eager, joinedload

from ....extensions import db
from ...models import AdminUserRecord, UserRecord, UserTokenRecord
from ..crud_service import CRUDService
from ..utils import retry_on_db_disconnect

logger = logging.getLogger(__name__)


class UserTokenService(CRUDService[UserTokenRecord]):
    """Stores and retrieves already-encrypted OAuth tokens."""

    def __init__(self) -> None:
        super().__init__(db.session, UserTokenRecord)

    @retry_on_db_disconnect()
    def get_authenticated_user_context(self, user_id: int) -> tuple[UserTokenRecord | None, bool]:
        """Load the token, its user, and the admin flags in one query.

        Returns:
            (token, is_active_admin), or None if the
            token or its user does not exist.
        """
        # Correlated EXISTS subqueries: evaluated per row, stop at first match,
        # and never multiply the result rows (unlike LEFT JOINs).
        is_admin = (
            exists()
            .where(
                AdminUserRecord.username == UserRecord.username,
                AdminUserRecord.is_active.is_(True),
            )
            .label("is_active_admin")
        )

        row = (
            self.session.query(UserTokenRecord, is_admin)
            .join(UserTokenRecord.user)  # INNER JOIN: skips tokens without a user
            .options(contains_eager(UserTokenRecord.user))  # reuse the join, no extra SELECT
            .filter(UserTokenRecord.user_id == user_id)
            .first()
        )

        if row is None:
            return None, False

        token, active_admin = row
        return token, bool(active_admin)

    def get_authenticated_user_token(self, user_id: int) -> None | UserTokenRecord:
        """Fetch the CurrentUser composite for session restoration."""
        token = (
            self.session.query(UserTokenRecord)
            .options(joinedload(UserTokenRecord.user))
            .filter(UserTokenRecord.user_id == user_id)
            .first()
        )
        if not token or not token.user:
            return None

        return token

    def upsert_user_token(
        self,
        user_id: int,
        encrypted_token: bytes,
        encrypted_secret: bytes,
    ) -> UserTokenRecord:
        """
        Upsert the encrypted OAuth credentials for a user.
        Creates a new token row if one does not exist.
        """
        instance, _ = self.upsert_by(
            {"user_id": user_id},
            access_token=encrypted_token,
            access_secret=encrypted_secret,
        )
        return instance

    def get_user_token_by_username(self, username: str) -> UserTokenRecord | None:
        return (
            self.session.query(UserTokenRecord)
            .join(UserRecord, UserTokenRecord.user_id == UserRecord.user_id)
            .filter(UserRecord.username == username)
            .first()
        )

    def update_last_used(self, user_id: int) -> UserTokenRecord | None:
        token = self.get_record_by_id(user_id)
        if token is None:
            return None

        return self.update(token, last_used_at=datetime.utcnow())

    def delete_token_by_user_id(self, user_id: int) -> bool:
        token = self.get_record_by_id(user_id)
        return self.delete_record(token) if token else False


__all__ = [
    "UserTokenService",
]
