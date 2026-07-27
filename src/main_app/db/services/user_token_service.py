"""
SQLAlchemy-based service for managing user tokens.
"""

from __future__ import annotations

import logging

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from ...extensions import db
from ...shared.core.crypto import encrypt_value
from ..models import UserTokenRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class UserTokenService(CRUDService[UserTokenRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, UserTokenRecord)

    def encrypt_value(self, value: str) -> bytes:
        return encrypt_value(value)

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

        user_id = int(user_id)
        orm_obj = self.get_record_by_id(user_id)
        if not orm_obj:
            return None
        return orm_obj

    def create_user_token(self, user_id: int, access_key: str, access_secret: str) -> UserTokenRecord:
        try:
            encrypted_token = self.encrypt_value(access_key)
            encrypted_secret = self.encrypt_value(access_secret)

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

    def update_user_token(self, user_id: int, access_key: str, access_secret: str) -> UserTokenRecord | None:
        """
        update the encrypted OAuth credentials for a user.
        """
        orm_obj = self.get_record_by_id(user_id)

        if not orm_obj:
            return None

        try:
            encrypted_token = self.encrypt_value(access_key)
            encrypted_secret = self.encrypt_value(access_secret)
            now = func.current_timestamp()

            orm_obj.access_token = encrypted_token
            orm_obj.access_secret = encrypted_secret
            orm_obj.updated_at = now
            orm_obj.last_used_at = now
            orm_obj.rotated_at = now

            self.session.commit()
            self.session.refresh(orm_obj)
            return orm_obj
        except Exception as exc:
            self.session.rollback()
            return None

    def upsert_user_token(
        self,
        user_id: int,
        access_key: str,
        access_secret: str,
    ) -> UserTokenRecord:
        """
        Upsert the encrypted OAuth credentials for a user.
        Creates a new token row if one does not exist.
        """
        try:
            record = self.get_record_by_id(user_id)
            if record:
                orm_obj = self.update_user_token(user_id, access_key, access_secret)
            else:
                orm_obj = self.create_user_token(user_id, access_key, access_secret)

            return orm_obj

        except Exception as exc:
            self.session.rollback()
            raise exc


__all__ = [
    "UserTokenService",
]
