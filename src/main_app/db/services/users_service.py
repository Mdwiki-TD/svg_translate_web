"""
SQLAlchemy-based service for managing users and user tokens.

Users table is the stable identity layer. Tokens are a child of users.
"""

from __future__ import annotations

import logging

from ...extensions import db
from ..exceptions import UserNotFoundError
from ..models import UserRecord
from .delete_service import delete_record_by_pk

logger = logging.getLogger(__name__)


class UsersService:
    def __init__(self) -> None:
        pass

    def list_users(self) -> list[UserRecord]:
        """Return all user identity records."""
        return db.session.query(UserRecord).all()

    def get_user(self, user_id: int) -> UserRecord | None:
        """Fetch a user by user_id."""
        if not user_id:
            return None
        return db.session.query(UserRecord).filter(UserRecord.user_id == int(user_id)).first()

    def get_user_by_username(self, username: str) -> UserRecord | None:
        """Fetch a user by username."""
        username = (username or "").strip()
        if not username:
            return None
        return db.session.query(UserRecord).filter(UserRecord.username == username).first()

    def create_user(self, username: str) -> UserRecord:
        """Create a user identity row. Idempotent — returns existing if present."""
        existing = db.session.query(UserRecord).filter(UserRecord.username == username).first()
        if existing:
            return existing
        record = UserRecord(username=username)
        db.session.add(record)
        try:
            db.session.commit()
            db.session.refresh(record)
        except Exception:
            db.session.rollback()
            # Handle potential race condition where user was created concurrently
            existing = db.session.query(UserRecord).filter(UserRecord.username == username).first()
            if existing:
                return existing
            raise
        return record

    def toggle_can_run_jobs(self, user_id: int, value: bool) -> UserRecord:
        """Toggle can_run_jobs."""
        record = self.get_user(user_id)

        if not record:
            raise UserNotFoundError("User record not found")

        record.can_run_jobs = value
        db.session.commit()
        db.session.refresh(record)

        return record

    def toggle_can_run_bg_jobs(self, user_id: int, value: bool) -> UserRecord:
        """Toggle can_run_bg_jobs."""
        record = self.get_user(user_id)

        if not record:
            raise UserNotFoundError("User record not found")

        record.can_run_bg_jobs = value
        db.session.commit()
        db.session.refresh(record)

        return record

    def delete(self, record_id: int) -> bool:
        return delete_record_by_pk(UserRecord, record_id)


__all__ = [
    "UsersService",
]
