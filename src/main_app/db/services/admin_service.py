"""

SQLAlchemy-based service for managing coordinators.

"""

from __future__ import annotations

import logging
from typing import List

from sqlalchemy.exc import IntegrityError

from ...extensions import db
from ..exceptions import UserNotFoundError
from ..models import AdminUserRecord
from .utils import db_guard, db_guard_rollback

logger = logging.getLogger(__name__)

# ── SELECT ───────────────────────────────────────────────


@db_guard(default_return=False, msg="Failed to check coordinator status")
def is_active_coordinator(username: str) -> bool:
    """Check whether a single username is an active coordinator."""
    return (
        db.session.query(AdminUserRecord)
        .filter(AdminUserRecord.username == username, AdminUserRecord.is_active)
        .first()
        is not None
    )


def list_coordinators() -> List[AdminUserRecord]:
    """
    Return all coordinators from the database.

    Returns a list of records, or an empty list on failure.
    """
    return db.session.query(AdminUserRecord).all()


def get_coordinator_by_id(coordinator_id: int) -> AdminUserRecord:
    """
    Get a coordinator by ID.
    """
    record = db.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
    if not record:
        raise LookupError(f"Coordinator id {coordinator_id} was not found")
    return record


# ── INSERT, UPDATE, SET ──────────────────────────────────


def add_coordinator(username: str) -> AdminUserRecord:
    """Add a coordinator."""

    if not username:
        raise ValueError("Username is required")

    record = db.session.query(AdminUserRecord).filter(AdminUserRecord.username == username).first()
    if record:
        # This assumes a UNIQUE constraint on the username column
        raise ValueError(f"Coordinator '{username}' already exists") from None

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
def set_coordinator_active(coordinator_id: int, is_active: bool) -> AdminUserRecord:
    """Toggle coordinator activity."""
    # record = get_coordinator_by_id(coordinator_id)
    record = db.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
    if record:
        record.is_active = is_active
        db.session.commit()
        db.session.refresh(record)
        return record


# ── DELETE ───────────────────────────────────────────────


@db_guard(default_return=False)
def delete_coordinator(coordinator_id: int) -> bool:
    """
    Delete a coordinator efficiently.

    Returns True if rows were affected, False otherwise (or on failure).
    """
    affected_rows = (
        db.session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).delete(synchronize_session=False)
    )
    db.session.commit()
    return affected_rows > 0


__all__ = [
    "add_coordinator",
    "delete_coordinator",
    "get_coordinator_by_id",
    "is_active_coordinator",
    "list_coordinators",
    "set_coordinator_active",
]
