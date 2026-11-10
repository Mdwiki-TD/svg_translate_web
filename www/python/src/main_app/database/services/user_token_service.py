"""
SQLAlchemy-based service for managing user tokens.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import joinedload

from ...extensions import db
from ..models import UserRecord, UserTokenRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class UserTokenService(CRUDService[UserTokenRecord]):
    """Stores and retrieves already-encrypted OAuth tokens."""

    def __init__(self) -> None:
        super().__init__(db.session, UserTokenRecord)

    def get_authenticated_user_token(self, user_id: int) -> None | UserTokenRecord:
        """Fetch the CurrentUser composite for session restoration."""
        try:
            token = (
                self.session.query(UserTokenRecord)
                .options(joinedload(UserTokenRecord.user))
                .filter(UserTokenRecord.user_id == user_id)
                .first()
            )
            if not token or not token.user:
                return None
            return token
        except Exception as e:
            logger.error("Error loading user for ID %s: %s", user_id, e)
            return None

    def upsert_user_token(
        self,
        user_id: int,
        encrypted_token: bytes,
        encrypted_secret: bytes,
    ) -> UserTokenRecord | None:
        """
        Upsert the encrypted OAuth credentials for a user.
        Creates a new token row if one does not exist.
        """
        try:
            instance, _ = self.upsert_by(
                {"user_id": user_id},
                access_token=encrypted_token,
                access_secret=encrypted_secret,
            )
            return instance
        except Exception as e:
            logger.exception("Error upserting user token: %s", e)
            return None

    def get_user_token_by_username(self, username: str) -> UserTokenRecord | None:
        try:
            return (
                self.session.query(UserTokenRecord)
                .join(UserRecord, UserTokenRecord.user_id == UserRecord.user_id)
                .filter(UserRecord.username == username)
                .first()
            )
        except Exception as exc:
            logger.error("Error getting token by username %s: %s", username, exc)
            return None

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
