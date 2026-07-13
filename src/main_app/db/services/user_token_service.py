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
from .utils import db_guard_rollback

logger = logging.getLogger(__name__)


# ── SELECT ───────────────────────────────────────────────


def get_authenticated_user_token(user_id: int) -> None | UserTokenRecord:
    """Fetch the CurrentUser composite for session restoration."""
    try:
        token = (
            db.session.query(UserTokenRecord)
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


def get_user_token(user_id: str | int) -> UserTokenRecord | None:
    """Fetch the encrypted OAuth credentials for a user."""
    if not user_id:
        return None

    user_id = int(user_id)
    orm_obj = db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()
    if not orm_obj:
        return None
    return orm_obj


# ── INSERT, UPDATE, SET ──────────────────────────────────


@db_guard_rollback
def create_user_token(user_id: int, access_key: str, access_secret: str) -> UserTokenRecord:
    """ """
    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)

    record = UserTokenRecord(
        user_id=user_id,
        access_token=encrypted_token,
        access_secret=encrypted_secret,
    )
    db.session.add(record)

    db.session.commit()
    db.session.refresh(record)

    return record


@db_guard_rollback
def update_user_token(user_id: int, access_key: str, access_secret: str) -> UserTokenRecord | None:
    """
    update the encrypted OAuth credentials for a user.
    """
    orm_obj = db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()

    if not orm_obj:
        return None

    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)
    now = func.current_timestamp()

    orm_obj.access_token = encrypted_token
    orm_obj.access_secret = encrypted_secret
    orm_obj.updated_at = now
    orm_obj.last_used_at = now
    orm_obj.rotated_at = now

    db.session.commit()
    db.session.refresh(orm_obj)
    return orm_obj


@db_guard_rollback
def upsert_user_token(
    user_id: int,
    access_key: str,
    access_secret: str,
) -> UserTokenRecord:
    """
    Upsert the encrypted OAuth credentials for a user.
    Creates a new token row if one does not exist.
    """

    # record = db.session.get(UserTokenRecord, user_id)
    record = db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()
    if record:
        orm_obj = update_user_token(user_id, access_key, access_secret)
    else:
        orm_obj = create_user_token(user_id, access_key, access_secret)

    return orm_obj


class UserTokenService:
    def __init__(self) -> None:
        pass

    def get_authenticated_user_token(self, user_id: int) -> None | UserTokenRecord:
        return get_authenticated_user_token(user_id)

    def get_user_token(self, user_id: str | int) -> UserTokenRecord | None:
        return get_user_token(user_id)

    def create_user_token(self, user_id: int, access_key: str, access_secret: str) -> UserTokenRecord:
        return create_user_token(user_id, access_key, access_secret)

    def update_user_token(self, user_id: int, access_key: str, access_secret: str) -> UserTokenRecord | None:
        return update_user_token(user_id, access_key, access_secret)

    def upsert_user_token(
        self,
        user_id: int,
        access_key: str,
        access_secret: str,
    ) -> UserTokenRecord:
        return upsert_user_token(user_id, access_key, access_secret)


__all__ = [
    "UserTokenService",
    "upsert_user_token",
    "get_user_token",
    "update_user_token",
]
