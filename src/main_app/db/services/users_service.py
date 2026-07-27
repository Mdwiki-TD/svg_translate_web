"""
SQLAlchemy-based service for managing users and user tokens.

Users table is the stable identity layer. Tokens are a child of users.
"""

from __future__ import annotations

import logging

from ...extensions import db
from ..exceptions import UserNotFoundError
from ..models import UserRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class UsersService(CRUDService[UserRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, UserRecord)

    def list_users(self) -> list[UserRecord]:
        """Return all user identity records."""
        return self.list_all()

    def get_user(self, user_id: int) -> UserRecord | None:
        """Fetch a user by user_id."""
        if not user_id:
            return None
        return self.get(user_id)

    def get_user_by_username(self, username: str) -> UserRecord | None:
        """Fetch a user by username."""
        username = (username or "").strip()
        if not username:
            return None
        return self.get_by(username=username)

    def create_user(self, username: str) -> UserRecord:
        """Create a user identity row. Idempotent — returns existing if present."""
        existing = self.get_by(username=username)
        if existing:
            return existing

        data = {"username": username}
        return self.create(**data)

    def toggle_can_run_jobs(self, user_id: int, value: bool) -> UserRecord:
        """Toggle can_run_jobs."""
        record = self.get_user(user_id)

        if not record:
            raise UserNotFoundError("User record not found")

        data = {"can_run_jobs": value}
        return self.update(record, **data)

    def toggle_can_run_bg_jobs(self, user_id: int, value: bool) -> UserRecord:
        """Toggle can_run_bg_jobs."""
        record = self.get_user(user_id)

        if not record:
            raise UserNotFoundError("User record not found")

        data = {"can_run_bg_jobs": value}
        return self.update(record, **data)


__all__ = [
    "UsersService",
]
