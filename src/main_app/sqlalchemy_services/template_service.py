from __future__ import annotations

import logging
from typing import List, Optional

from ..sqlalchemy_models.templates import TemplateRecord
from ..engine import get_session

logger = logging.getLogger(__name__)


def get_template(template_id: int) -> Optional[TemplateRecord]:
    """Fetch a template by ID."""
    with get_session() as session:
        return session.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()


def get_template_by_title(title: str) -> Optional[TemplateRecord]:
    """Fetch a template by title."""
    with get_session() as session:
        return session.query(TemplateRecord).filter(TemplateRecord.title == title).first()


def list_templates(limit: int = 100) -> List[TemplateRecord]:
    """List templates."""
    with get_session() as session:
        return session.query(TemplateRecord).order_by(TemplateRecord.title).limit(limit).all()


def upsert_template(template_data: dict) -> TemplateRecord:
    """Insert or update a template."""
    title = template_data.get("title")
    with get_session() as session:
        template = session.query(TemplateRecord).filter(TemplateRecord.title == title).first()
        if template:
            for key, value in template_data.items():
                setattr(template, key, value)
        else:
            template = TemplateRecord(**template_data)
            session.add(template)
        session.commit()
        session.refresh(template)
        return template


__all__ = [
    "get_template",
    "get_template_by_title",
    "list_templates",
    "upsert_template",
]
