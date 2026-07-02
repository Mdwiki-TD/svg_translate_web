from __future__ import annotations

import logging
from typing import Any, List

from sqlalchemy import cast, func, String, select
from ...extensions import db
from ..models.templates import TemplateRecord
from ..templates_utils import ensure_template_data
from .utils import db_guard

logger = logging.getLogger(__name__)


# ── SELECT ───────────────────────────────────────────────


def list_templates(limit: int | None = None) -> List[TemplateRecord]:
    """Return all templates"""
    query = db.session.query(TemplateRecord).order_by(TemplateRecord.title)
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def list_templates_mismatched_years() -> List[TemplateRecord]:
    """
    Fetches all template records where the 'last_world_file'
    does not contain the 'last_world_year', resolving collation conflicts.
    """
    # Define the target collation causing the issue
    target_collation = "utf8mb4_unicode_ci"

    # Cast and force the collation on the concatenated string
    search_pattern = func.concat(
        '%',
        cast(TemplateRecord.last_world_year, String),
        '%'
    ).collate(target_collation)

    # Construct the query
    stmt = select(TemplateRecord).where(
        TemplateRecord.last_world_file.not_like(search_pattern)
    )

    results = db.session.scalars(stmt).all()
    return list(results)


def get_template(template_id: int) -> TemplateRecord:
    """Fetch a template by ID."""
    return db.session.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()


def get_template_by_title(title: str) -> TemplateRecord:
    """Fetch a template by title."""
    return db.session.query(TemplateRecord).filter(TemplateRecord.title == title).first()


# ── INSERT, UPDATE, SET ──────────────────────────────────


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

    data = ensure_template_data(data)

    temp_data = {key: value for key, value in data.items() if value is not None and hasattr(TemplateRecord, key)}
    record = TemplateRecord(**temp_data)

    db.session.add(record)

    try:
        db.session.commit()
        db.session.refresh(record)
    except Exception as exc:
        db.session.rollback()
        raise exc

    return record


@db_guard(default_return=None)
def update_template_data(
    template_id: int,
    template_data: dict[str, str],
) -> TemplateRecord | None:
    """
    Update template only if not None.
    """
    template = db.session.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()
    if not template:
        return None

    template_data = ensure_template_data(template_data)

    for key, value in template_data.items():
        if value is not None:
            setattr(template, key, value)

    db.session.commit()
    db.session.refresh(template)

    return template


__all__ = [
    "get_template_by_title",
    "add_template_data",
    "update_template_data",
    "list_templates",
    "list_templates_mismatched_years",
    "get_template",
]
