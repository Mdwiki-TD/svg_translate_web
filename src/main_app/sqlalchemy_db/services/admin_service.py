"""Utilities for managing administrator (coordinator) accounts."""

from __future__ import annotations

import logging
from typing import List

from ..engine import get_session
from ..models import AdminUserRecord

logger = logging.getLogger(__name__)


def list_coordinators() -> List[AdminUserRecord]:
    """Return all coordinators."""
    with get_session() as session:
        return session.query(AdminUserRecord).all()


def active_coordinators() -> list[str]:
    """Return usernames of all active coordinators."""
    with get_session() as session:
        return [u.username for u in session.query(AdminUserRecord).filter(AdminUserRecord.is_active).all()]


def get_coordinator_by_id(coordinator_id: int) -> AdminUserRecord:
    """
    Get a coordinator by ID.
    """
    with get_session() as session:
        record = session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
        if not record:
            raise LookupError(f"Coordinator id {coordinator_id} was not found")
        return record


def add_coordinator(username: str) -> AdminUserRecord:
    """Add a coordinator."""

    if not username:
        raise ValueError("Username is required")

    with get_session() as session:
        record = session.query(AdminUserRecord).filter(AdminUserRecord.username == username).first()
        if record:
            # This assumes a UNIQUE constraint on the username column
            raise ValueError(f"Coordinator '{username}' already exists") from None

        record = AdminUserRecord(username=username, is_active=True)
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def set_coordinator_active(coordinator_id: int, is_active: bool) -> AdminUserRecord:
    """Toggle coordinator activity."""
    with get_session() as session:
        # record = get_coordinator_by_id(coordinator_id)
        record = session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()

        record.is_active = is_active
        session.commit()
        session.refresh(record)
        return record


def delete_coordinator(coordinator_id: int) -> bool:
    """Delete a coordinator."""
    with get_session() as session:
        # record = get_coordinator_by_id(coordinator_id)
        record = session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()

        if record:
            session.delete(record)
            session.commit()
            return True
        return False


__all__ = [
    "get_coordinator_by_id",
    "list_coordinators",
    "active_coordinators",
    "add_coordinator",
    "set_coordinator_active",
    "delete_coordinator",
]
