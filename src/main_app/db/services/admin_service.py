"""

SQLAlchemy-based service for managing coordinators.

"""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError

from ...extensions import db
from ..exceptions import DuplicateUserError, UserNotFoundError
from ..models import AdminUserRecord
from .delete_service import delete_record_by_pk
from .utils import db_guard_rollback

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self) -> None:
        pass

    def is_active_coordinator(self, username: str) -> bool:
        """Check whether a single username is an active coordinator."""
        try:
            record = (
                db.session.query(AdminUserRecord)
                .filter(AdminUserRecord.username == username, AdminUserRecord.is_active)
                .first()
            )
            return record is not None
        except Exception:
            logger.exception("Failed to check coordinator status")
        return False

    def list_coordinators(self) -> list[AdminUserRecord]:
        """
        Return all coordinators from the database.

        Returns a list of records, or an empty list on failure.
        """
        return db.session.query(AdminUserRecord).all()

    def get_coordinator_by_id(self, coordinator_id: int) -> AdminUserRecord:
        """
        Get a coordinator by ID.
        """
        record = db.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
        if not record:
            raise LookupError(f"Coordinator id {coordinator_id} was not found")
        return record

    def add_coordinator(self, username: str) -> AdminUserRecord:
        """Add a coordinator."""
        if not username or not username.strip():
            raise ValueError("Username is required")
        username = username.strip()

        record = db.session.query(AdminUserRecord).filter(AdminUserRecord.username == username).first()
        if record:
            raise DuplicateUserError(f"Coordinator '{username}' already exists") from None

        record = AdminUserRecord(username=username, is_active=True)
        db.session.add(record)
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            if "a foreign key constraint fails" in str(exc):
                raise UserNotFoundError(f"User '{username}' does not exist") from exc
            raise
        db.session.refresh(record)
        return record

    @db_guard_rollback
    def set_coordinator_active(self, coordinator_id: int, is_active: bool) -> AdminUserRecord | None:
        """Toggle coordinator activity."""
        record = db.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
        if not record:
            return None

        record.is_active = is_active
        db.session.commit()
        db.session.refresh(record)
        return record

    def delete(self, record_id: int) -> bool:
        return delete_record_by_pk(AdminUserRecord, record_id)


__all__ = [
    "AdminService",
]
