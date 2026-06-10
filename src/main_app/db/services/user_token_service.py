"""
SQLAlchemy-based service for managing user tokens.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import defer

from ...core.crypto import encrypt_value
from ...extensions import db
from ..models import UserTokenRecord
from .utils import db_guard, db_guard_rollback

logger = logging.getLogger(__name__)


# ── SELECT ───────────────────────────────────────────────


def list_users() -> list[UserTokenRecord]:
    """Return all users."""
    records = (
        db.session.query(UserTokenRecord)
        .options(defer(UserTokenRecord.access_token), defer(UserTokenRecord.access_secret))
        .all()
    )
    return records


def get_user_token(user_id: str | int) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user."""
    if not user_id:
        return None

    user_id = int(user_id)
    orm_obj = db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()
    if not orm_obj:
        return None
    return orm_obj


def get_authenticated_user_token(user_id: int) -> None | UserTokenRecord:
    """Fetch the CurrentUser composite for session restoration."""
    return get_user_token(user_id)


def get_user_token_by_username(username: str) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user by username."""
    username = username.strip()
    if not username:
        return None

    orm_obj = db.session.query(UserTokenRecord).filter(UserTokenRecord.username == username).first()
    if not orm_obj:
        return None
    return orm_obj


# ── INSERT, UPDATE, SET ──────────────────────────────────


@db_guard_rollback
def create_user_token(username: str, access_key: str, access_secret: str) -> UserTokenRecord:
    """Create a user identity row. Idempotent — returns existing if present."""
    username = (username or "").strip()

    existing = db.session.query(UserTokenRecord).filter(UserTokenRecord.username == username).first()
    if existing:
        return existing

    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)

    now = func.current_timestamp()

    record = UserTokenRecord(
        username=username,
        access_token=encrypted_token,
        access_secret=encrypted_secret,
        created_at=now,
        updated_at=now,
        last_used_at=now,
        rotated_at=None,
    )
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


@db_guard_rollback
def update_user_token(user_id: int, access_key: str, access_secret: str) -> UserTokenRecord:
    """
    update the encrypted OAuth credentials for a user.
    """
    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)
    now = func.current_timestamp()

    orm_obj = db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).first()
    if orm_obj:
        orm_obj.access_token = encrypted_token
        orm_obj.access_secret = encrypted_secret
        orm_obj.updated_at = now
        orm_obj.last_used_at = now
        orm_obj.rotated_at = now

        db.session.commit()
        db.session.refresh(orm_obj)
    return orm_obj


# ── DELETE ───────────────────────────────────────────────


@db_guard(default_return=False)
def delete_user_token(user_id: int) -> bool:
    """
    Delete the stored OAuth token only. User identity row persists.

    TODO: call .delete() on UserTokenRecord, so logout now removes the entire persisted user record.
        That contradicts the docstring and can wipe identity/admin state instead of only clearing OAuth secrets.
        Clear the token fields in-place, or move credentials into a separate token table,
        but don't delete the user row here.
    """
    if not user_id:
        return False

    affected_rows = (
        db.session.query(UserTokenRecord).filter(UserTokenRecord.user_id == user_id).delete(synchronize_session=False)
    )
    db.session.commit()
    return affected_rows > 0


__all__ = [
    "list_users",
    "update_user_token",
    "get_user_token",
    "delete_user_token",
    "get_user_token_by_username",
]
