"""
SQLAlchemy-based service for managing users and user tokens.

Users table is the stable identity layer. Tokens are a child of users.
"""

from __future__ import annotations

import logging
from typing import Optional

from ...extensions import db
from ..exceptions import UserNotFoundError
from ..models import UsersRecord
from .utils import db_guard

logger = logging.getLogger(__name__)

# ── SELECT ───────────────────────────────────────────────


def list_users() -> list[UsersRecord]:
    """Return all user identity records."""
    return db.session.query(UsersRecord).all()


def get_user(user_id: int) -> Optional[UsersRecord]:
    """Fetch a user by user_id."""
    if not user_id:
        return None
    return db.session.query(UsersRecord).filter(UsersRecord.user_id == int(user_id)).first()


def get_user_by_username(username: str) -> Optional[UsersRecord]:
    """Fetch a user by username."""
    username = (username or "").strip()
    if not username:
        return None
    return db.session.query(UsersRecord).filter(UsersRecord.username == username).first()


# ── INSERT, UPDATE, SET ──────────────────────────────────


def create_user(username: str) -> UsersRecord:
    """Create a user identity row. Idempotent — returns existing if present."""
    existing = db.session.query(UsersRecord).filter(UsersRecord.username == username).first()
    if existing:
        return existing
    record = UsersRecord(username=username)
    db.session.add(record)
    try:
        db.session.commit()
        db.session.refresh(record)
    except Exception:
        db.session.rollback()
        # Handle potential race condition where user was created concurrently
        existing = db.session.query(UsersRecord).filter(UsersRecord.username == username).first()
        if existing:
            return existing
        raise
    return record


def toggle_can_run_jobs(user_id: int, value: bool) -> UsersRecord:
    """Toggle can_run_jobs."""
    record = get_user(user_id)

    if not record:
        raise UserNotFoundError("User record not found")

    record.can_run_jobs = value
    db.session.commit()
    db.session.refresh(record)

    return record


def toggle_can_run_bg_jobs(user_id: int, value: bool) -> UsersRecord:
    """Toggle can_run_bg_jobs."""
    record = get_user(user_id)

    if not record:
        raise UserNotFoundError("User record not found")

    record.can_run_bg_jobs = value
    db.session.commit()
    db.session.refresh(record)

    return record


# ── DELETE ───────────────────────────────────────────────


@db_guard(default_return=False)
def delete_user(user_id: int) -> bool:
    """Delete user row. Cascades to user_tokens and admin_users via FK."""
    if not user_id:
        return False
    affected = db.session.query(UsersRecord).filter(UsersRecord.user_id == user_id).delete()
    db.session.commit()
    return affected > 0


__all__ = [
    "create_user",
    "delete_user",
    "get_user",
    "get_user_by_username",
    "list_users",
]
