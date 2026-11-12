"""

SQLAlchemy-based service for managing admins.

"""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError

from ...extensions import db
from ..exceptions import DuplicateRecordError, UserNotFoundError
from ..models import AdminUserRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class AdminService(CRUDService[AdminUserRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, AdminUserRecord)

    def is_active_admin(self, username: str) -> bool:
        """Check whether a single username is an active admin."""
        try:
            record = (
                self.session.query(AdminUserRecord)
                .filter(AdminUserRecord.username == username, AdminUserRecord.is_active)
                .first()
            )
            return record is not None
        except Exception:
            logger.exception("Failed to check admin status")
        return False

    def list_admins(self) -> list[AdminUserRecord]:
        return self.list_all()

    def get_admin_by_id(self, admin_id: int) -> AdminUserRecord:
        """
        Get an admin by ID.
        """
        record = self.get_record_by_id(admin_id)

        if not record:
            raise LookupError(f"Admin id {admin_id} was not found")
        return record

    def add_admin(self, username: str) -> AdminUserRecord:
        if not username or not username.strip():
            raise ValueError("Username is required")
        username = username.strip()

        """Add an admin."""
        record = self.session.query(AdminUserRecord).filter(AdminUserRecord.username == username).first()
        if record:
            # This assumes a UNIQUE constraint on the username column
            raise DuplicateRecordError(f"Admin '{username}' already exists") from None

        record = AdminUserRecord(username=username, is_active=True)

        try:
            self.session.add(record)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            error_message = str(exc).lower()
            if "foreign key constraint" in error_message:
                raise UserNotFoundError(f"User '{username}' does not exist") from exc

            if "Duplicate entry" in str(exc.orig) or "UNIQUE constraint failed" in str(exc.orig):
                raise DuplicateRecordError(f"Admin '{username}' already exists") from exc

            raise

        try:
            self.session.refresh(record)
        except Exception:
            self.session.rollback()
            raise

        return record

    def set_admin_active(self, admin_id: int, is_active: bool) -> AdminUserRecord | None:
        """Toggle admin activity."""
        # record = get_admin_by_id(admin_id)
        record = self.get_record_by_id(admin_id)
        if not record:
            return None

        try:
            record.is_active = is_active
            self.session.commit()
            self.session.refresh(record)
            return record
        except Exception:
            self.session.rollback()
            return None


__all__ = [
    "AdminService",
]
