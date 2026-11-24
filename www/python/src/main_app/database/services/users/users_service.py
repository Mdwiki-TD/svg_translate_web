"""
SQLAlchemy-based service for managing users.
"""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...db_base import db
from ...models import UserRecord
from ..crud_service import CRUDService

logger = logging.getLogger(__name__)


class UsersService(CRUDService[UserRecord]):
    """CRUD + domain-specific queries for user records."""

    model = UserRecord

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(session=session or db.session)

    def list_users(self) -> list[UserRecord]:
        """Return all user identity records."""
        return self.list_all()

    def get_user(self, user_id: int) -> UserRecord | None:
        """Fetch a user by user_id."""
        if not user_id:
            return None
        return self.get_record_by_id(user_id)

    def get_user_by_username(self, username: str) -> UserRecord | None:
        """Fetch a user by username."""
        username = (username or "").strip()
        if not username:
            return None
        return self.get_by(username=username)

    def create_user(self, username: str) -> None | UserRecord:
        """Create a user identity row. Idempotent — returns existing if present."""
        return self.get_by(username=username) or self.create(username=username)

    def ensure_exists(self, username: str) -> UserRecord:
        """Create a UserRecord if one doesn't exist. Returns the record.

        Handles concurrent-create races (IntegrityError) by retrying
        as a fetch, following the pattern from mdwiki.org_scripts.
        """
        record = self.get_user_by_username(username)
        if record is not None:
            return record
        try:
            return self.create(username=username)
        except IntegrityError:
            # Race condition: another request created the same record
            self.session.rollback()
            record = self.get_user_by_username(username)
            if record is not None:
                return record
            raise


__all__ = [
    "UsersService",
]
