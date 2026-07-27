from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import String, cast, func, select

from ...extensions import db
from ..exceptions import DuplicateRecordError
from ..models.templates import TemplateRecord
from ..templates_utils import ensure_template_data
from .crud_service import CRUDService
from .utils import db_guard

logger = logging.getLogger(__name__)


# ── SELECT ───────────────────────────────────────────────


def _list_templates_mismatched_years() -> list[TemplateRecord]:
    """
    Fetches all template records where the 'last_world_file'
    does not contain the 'last_world_year', resolving collation conflicts.
    """
    # Define the target collation causing the issue
    target_collation = "utf8mb4_unicode_ci"

    # Cast and force the collation on the concatenated string
    search_pattern = func.concat("%", cast(TemplateRecord.last_world_year, String), "%")

    # SQLite does not support mysql collations, so only apply collate on mysql/mariadb
    if db.engine.dialect.name == "mysql":
        search_pattern = search_pattern.collate(target_collation)

    # Construct the query, ensuring we only compare non-null values
    stmt = select(TemplateRecord).where(
        TemplateRecord.last_world_file.is_not(None),
        TemplateRecord.last_world_year.is_not(None),
        TemplateRecord.last_world_file.not_like(search_pattern),
    )

    results = db.session.scalars(stmt).all()
    return list(results)


# ── INSERT, UPDATE, SET ──────────────────────────────────


def _add_template_data(data: dict[str, Any]) -> TemplateRecord:
    """
    Add a new template.
    """
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
def _update_template_data(
    template_id: int,
    template_data: dict[str, str],
) -> TemplateRecord | None:
    """
    Update template only if not None.
    """
    template = db.session.query(TemplateRecord).filter(TemplateRecord.id == template_id).first()
    if not template:
        return None

    for key, value in template_data.items():
        if value is not None and hasattr(template, key):
            setattr(template, key, value)

    db.session.commit()
    db.session.refresh(template)

    return template


class TemplateService(CRUDService[TemplateRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, TemplateRecord)

    def list(self, limit: int | None = None) -> list[TemplateRecord]:
        return super().list(
            limit=limit,
            order_by=[TemplateRecord.title],
        )

    def list_templates_mismatched_years(self) -> list[TemplateRecord]:
        return _list_templates_mismatched_years()

    def get_template(self, template_id: int) -> TemplateRecord | None:
        return self.get(template_id)

    def get_template_by_title(self, title: str) -> TemplateRecord | None:
        return self.get_by(
            title=title,
        )

    def add_template_data(self, data: dict[str, Any]) -> TemplateRecord | None:
        title = data.get("title", "")
        if not title or not title.strip():
            raise ValueError("Title is required")

        existing = self.get_template_by_title(title)
        if existing:
            raise DuplicateRecordError(f"Template '{title}' already exists")

        data = ensure_template_data(data)
        return self.create(commit=True, **data)

    def update_template_data(
        self,
        template_id: int,
        template_data: dict[str, str],
    ) -> TemplateRecord | None:
        template_data = ensure_template_data(template_data)
        return self.update_by_id(pk=template_id, data=template_data)


__all__ = [
    "TemplateService",
]
