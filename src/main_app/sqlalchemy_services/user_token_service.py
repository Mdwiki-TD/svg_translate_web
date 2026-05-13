"""
SQLAlchemy-based service for managing user tokens.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ...sqlalchemy_models import UserTokenRecord
from ..core.crypto import encrypt_value
from ..engine import get_session

logger = logging.getLogger(__name__)


def upsert_user_token(*, user_id: int, username: str, access_key: str, access_secret: str) -> None:
    """Insert or update the encrypted OAuth credentials for a user."""
    username = username.strip()
    if not username:
        raise ValueError("Username is required")

    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)
    now = func.current_timestamp()

    with get_session() as session:
        orm_obj = session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()
        if orm_obj:
            orm_obj.username = username
            orm_obj.access_token = encrypted_token
            orm_obj.access_secret = encrypted_secret
            orm_obj.updated_at = now
            orm_obj.last_used_at = now
            orm_obj.rotated_at = now
        else:
            orm_obj = UserTokenRecord(
                user_id=user_id,
                username=username,
                access_token=encrypted_token,
                access_secret=encrypted_secret,
                created_at=now,
                updated_at=now,
                last_used_at=now,
            )
            session.add(orm_obj)

        session.commit()


def get_user_token(user_id: str | int) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user."""
    if not user_id:
        return None

    user_id = int(user_id)
    with get_session() as session:
        orm_obj = session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()
        if not orm_obj:
            return None
        return orm_obj


def delete_user_token(user_id: int) -> None:
    """Remove the stored OAuth credentials for the given user id."""
    if not user_id:
        return

    with get_session() as session:
        session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).delete()
        session.commit()


def get_user_token_by_username(username: str) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user by username."""
    username = username.strip()
    if not username:
        return None

    with get_session() as session:
        orm_obj = session.query(UserTokenRecord).filter(UserTokenRecord.username == username).first()
        if not orm_obj:
            return None
        return orm_obj


def delete_user_token_by_username(username: str) -> None:
    """Remove the stored OAuth credentials for the given username."""
    username = username.strip()
    if not username:
        return

    with get_session() as session:
        session.query(UserTokenRecord).filter(UserTokenRecord.username == username).delete()
        session.commit()


__all__ = [
    "upsert_user_token",
    "get_user_token",
    "delete_user_token",
    "get_user_token_by_username",
    "delete_user_token_by_username",
]
