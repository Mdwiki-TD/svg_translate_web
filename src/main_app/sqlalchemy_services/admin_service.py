from __future__ import annotations

import logging
from typing import List, Optional

from ..sqlalchemy_models.admin_users import AdminUserRecord
from ..engine import get_session

logger = logging.getLogger(__name__)


def list_coordinators() -> List[AdminUserRecord]:
    """Return all coordinators."""
    with get_session() as session:
        return session.query(AdminUserRecord).all()


def active_coordinators() -> List[str]:
    """Return usernames of all active coordinators."""
    with get_session() as session:
        return [u.username for u in session.query(AdminUserRecord).filter(AdminUserRecord.is_active == True).all()]


def add_coordinator(username: str) -> AdminUserRecord:
    """Add a coordinator."""
    with get_session() as session:
        record = session.query(AdminUserRecord).filter(AdminUserRecord.username == username).first()
        if record:
            record.is_active = True
        else:
            record = AdminUserRecord(username=username, is_active=True)
            session.add(record)
        session.commit()
        session.refresh(record)
        return record


def set_coordinator_active(coordinator_id: int, is_active: bool) -> Optional[AdminUserRecord]:
    """Toggle coordinator activity."""
    with get_session() as session:
        record = session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
        if record:
            record.is_active = is_active
            session.commit()
            session.refresh(record)
        return record


def delete_coordinator(coordinator_id: int) -> bool:
    """Delete a coordinator."""
    with get_session() as session:
        record = session.query(AdminUserRecord).filter(AdminUserRecord.id == coordinator_id).first()
        if record:
            session.delete(record)
            session.commit()
            return True
        return False


__all__ = [
    "list_coordinators",
    "active_coordinators",
    "add_coordinator",
    "set_coordinator_active",
    "delete_coordinator",
]
