from __future__ import annotations

import logging
from typing import List, Optional, Any
import json

from ..sqlalchemy_models.tasks import TaskRecord
from ..sqlalchemy_models.task_stages import TaskStageRecord
from ..engine import get_session

logger = logging.getLogger(__name__)


def create_task(task_id: str, title: str, normalized_title: str, status: str, username: Optional[str] = None) -> TaskRecord:
    """Create a new task."""
    with get_session() as session:
        task = TaskRecord(
            id=task_id,
            title=title,
            normalized_title=normalized_title,
            status=status,
            username=username
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def get_task(task_id: str) -> Optional[TaskRecord]:
    """Fetch a task by ID."""
    with get_session() as session:
        return session.query(TaskRecord).filter(TaskRecord.id == task_id).first()


def update_task_status(task_id: str, status: str) -> Optional[TaskRecord]:
    """Update task status."""
    with get_session() as session:
        task = session.query(TaskRecord).filter(TaskRecord.id == task_id).first()
        if task:
            task.status = status
            session.commit()
            session.refresh(task)
        return task


def add_task_stage(
    stage_id: str,
    task_id: str,
    stage_name: str,
    stage_number: int,
    stage_status: str,
    stage_message: Optional[str] = None
) -> TaskStageRecord:
    """Add or update a task stage."""
    with get_session() as session:
        stage = session.query(TaskStageRecord).filter(TaskStageRecord.stage_id == stage_id).first()
        if stage:
            stage.stage_status = stage_status
            stage.stage_message = stage_message
        else:
            stage = TaskStageRecord(
                stage_id=stage_id,
                task_id=task_id,
                stage_name=stage_name,
                stage_number=stage_number,
                stage_status=stage_status,
                stage_message=stage_message
            )
            session.add(stage)
        session.commit()
        session.refresh(stage)
        return stage


def get_task_stages(task_id: str) -> List[TaskStageRecord]:
    """List stages for a task."""
    with get_session() as session:
        return session.query(TaskStageRecord).filter(TaskStageRecord.task_id == task_id).order_by(TaskStageRecord.stage_number).all()


__all__ = [
    "create_task",
    "get_task",
    "update_task_status",
    "add_task_stage",
    "get_task_stages",
]
