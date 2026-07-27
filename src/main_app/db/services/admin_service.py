"""

SQLAlchemy-based service for managing coordinators.

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
        super().__init__(AdminUserRecord)

    def is_active_coordinator(self, username: str) -> bool:
        """Check whether a single username is an active coordinator."""
        try:
            record = (
                self.session.query(AdminUserRecord)
                .filter(AdminUserRecord.username == username, AdminUserRecord.is_active)
                .first()
            )
            return record is not None
        except Exception:
            logger.exception("Failed to check coordinator status")
        return False

    def list_coordinators(self) -> list[AdminUserRecord]:
        return self.list_all()

    def get_coordinator_by_id(self, coordinator_id: int) -> AdminUserRecord:
        """
        Get a coordinator by ID.
        """
        record = self.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()

        if not record:
            raise LookupError(f"Coordinator id {coordinator_id} was not found")
        return record

    def add_coordinator(self, username: str) -> AdminUserRecord:
        if not username or not username.strip():
            raise ValueError("Username is required")
        username = username.strip()

        """Add a coordinator."""
        record = self.session.query(AdminUserRecord).filter(AdminUserRecord.username == username).first()
        if record:
            # This assumes a UNIQUE constraint on the username column
            raise DuplicateRecordError(f"Coordinator '{username}' already exists") from None

        record = AdminUserRecord(username=username, is_active=True)
        self.session.add(record)
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            if "a foreign key constraint fails" in str(exc):
                raise UserNotFoundError(f"User '{username}' does not exist") from exc
            raise
        self.session.refresh(record)
        return record

    def set_coordinator_active(self, coordinator_id: int, is_active: bool) -> AdminUserRecord | None:
        """Toggle coordinator activity."""
        # record = get_coordinator_by_id(coordinator_id)
        try:
            record = self.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
            if not record:
                return None

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
