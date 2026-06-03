from __future__ import annotations

import logging
from typing import Any, List

from ...extensions import db
from ...utils.wikitext.titles_utils import match_last_world_year
from ..models.templates import TemplateRecord

logger = logging.getLogger(__name__)


def _ensure_last_world_year(template_data):
    if template_data.get("last_world_file") and not template_data.get("last_world_year"):
        template_data["last_world_year"] = match_last_world_year(template_data["last_world_file"])

    if template_data.get("slug") and "/grapher/" in template_data["slug"]:
        template_data["slug"] = template_data["slug"].split("/grapher/", maxsplit=1)[1].split("?")[0]

    return template_data


def list_templates(limit: int | None = None) -> List[TemplateRecord]:
    """Return all templates"""
    query = db.session.query(TemplateRecord).order_by(TemplateRecord.title)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def get_template(template_id: int) -> TemplateRecord:
    """Fetch a template by ID."""
    return db.session.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()


def get_template_by_title(title: str) -> TemplateRecord:
    """Fetch a template by title."""
    return db.session.query(TemplateRecord).filter(TemplateRecord.title == title).first()


def add_template_data(
    data: dict[str, Any],
) -> TemplateRecord:
    """
    Add a new template.
    """
    title = data.get("title", "")
    if not title or not title.strip():
        raise ValueError("Title is required")

    existing = db.session.query(TemplateRecord).filter(TemplateRecord.title == title).first()
    if existing:
        raise ValueError(f"Template '{title}' already exists")

    data = _ensure_last_world_year(data)

    chart = TemplateRecord(**data)

    db.session.add(chart)
    db.session.commit()
    db.session.refresh(chart)

    return chart


def update_template_data(
    template_id: int,
    template_data: dict[str, str],
) -> TemplateRecord:
    """
    Update template only if not None.
    """
    template_data = _ensure_last_world_year(template_data)
    template = db.session.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()
    if template:
        for key, value in template_data.items():
            if value is not None:
                setattr(template, key, value)
        db.session.commit()
        db.session.refresh(template)
    return template


def delete_template(template_id: int) -> bool:
    """Delete a template."""
    record = db.session.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()

    if record:
        db.session.delete(record)
        db.session.commit()
        return True
    return False


__all__ = [
    "get_template_by_title",
    "add_template_data",
    "update_template_data",
    "list_templates",
    "delete_template",
    "get_template",
]
