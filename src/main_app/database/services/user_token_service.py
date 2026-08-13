"""
SQLAlchemy-based service for managing user tokens.
"""

from __future__ import annotations

import logging

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from ...extensions import db
from ...services.core.crypto import encrypt_value
from ..models import UserRecord, UserTokenRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class UserTokenService(CRUDService[UserTokenRecord]):
    """Stores and retrieves already-encrypted OAuth tokens."""

    def __init__(self) -> None:
        super().__init__(db.session, UserTokenRecord)

    def encrypt_value(self, plaintext: str) -> bytes:
        return encrypt_value(plaintext=plaintext)

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

    def get_user_token(self, user_id: str | int) -> UserTokenRecord | None:
        """Fetch the encrypted OAuth credentials for a user."""
        if not user_id:
            return None
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            logger.warning("Invalid user_id for token lookup: %r", user_id)
            return None
        return self.get_record_by_id(user_id)

    def create_user_token(
        self,
        user_id: int,
        encrypted_token: bytes,
        encrypted_secret: bytes,
    ) -> UserTokenRecord:
        try:
            record = UserTokenRecord(
                user_id=user_id,
                access_token=encrypted_token,
                access_secret=encrypted_secret,
            )
            self.session.add(record)

            self.session.commit()
            self.session.refresh(record)

            return record
        except Exception as exc:
            self.session.rollback()
            raise exc

    def update_user_token(
        self,
        orm_obj: UserTokenRecord,
        encrypted_token: bytes,
        encrypted_secret: bytes,
    ) -> UserTokenRecord | None:
        """
        update the encrypted OAuth credentials for a user.
        """
        now = func.current_timestamp()
        data = {
            "access_token": encrypted_token,
            "access_secret": encrypted_secret,
            "updated_at": now,
            "last_used_at": now,
            "rotated_at": now,
        }
        try:
            self.update(orm_obj, **data)
            return orm_obj
        except Exception as exc:
            logger.error("Error updating token for user %s: %s", orm_obj.user_id, exc)
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
        record = self.get_record_by_id(user_id)
        if record:
            return self.update_user_token(record, encrypted_token, encrypted_secret)
        else:
            return self.create_user_token(user_id, encrypted_token, encrypted_secret)

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


__all__ = [
    "UserTokenService",
]
