from __future__ import annotations

import logging
from typing import List, Optional

from ..sqlalchemy_models.fix_nested_tasks import FixNestedTaskRecord
from ..engine import get_session

logger = logging.getLogger(__name__)


def create_fix_nested_task(task_id: str, filename: str, status: str, username: Optional[str] = None) -> FixNestedTaskRecord:
    """Create a fix nested task."""
    with get_session() as session:
        task = FixNestedTaskRecord(
            id=task_id,
            filename=filename,
            status=status,
            username=username
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def get_fix_nested_task(task_id: str) -> Optional[FixNestedTaskRecord]:
    """Fetch a fix nested task by ID."""
    with get_session() as session:
        return session.query(FixNestedTaskRecord).filter(FixNestedTaskRecord.id == task_id).first()


def update_fix_nested_task(task_id: str, **kwargs) -> Optional[FixNestedTaskRecord]:
    """Update a fix nested task."""
    with get_session() as session:
        task = session.query(FixNestedTaskRecord).filter(FixNestedTaskRecord.id == task_id).first()
        if task:
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            session.commit()
            session.refresh(task)
        return task


def list_fix_nested_tasks(limit: int = 100) -> List[FixNestedTaskRecord]:
    """List recent fix nested tasks."""
    with get_session() as session:
        return session.query(FixNestedTaskRecord).order_by(FixNestedTaskRecord.created_at.desc()).limit(limit).all()


__all__ = [
    "create_fix_nested_task",
    "get_fix_nested_task",
    "update_fix_nested_task",
    "list_fix_nested_tasks",
]
