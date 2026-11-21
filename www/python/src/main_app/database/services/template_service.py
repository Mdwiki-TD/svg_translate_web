from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import String, cast, func, select
from sqlalchemy.orm import Session

from ..db_base import db
from ..exceptions import DuplicateRecordError
from ..models.templates import TemplateRecord
from ..templates_utils import ensure_template_data
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class TemplateService(CRUDService[TemplateRecord]):
    model = TemplateRecord

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(session=session or db.session)

    def list(self, limit: int | None = None) -> list[TemplateRecord]:
        return super().list(
            limit=limit,
            order_by=[TemplateRecord.title],
        )

    def list_templates_mismatched_years(self) -> list[TemplateRecord]:
        """Templates whose 'last_world_file' does not contain 'last_world_year'."""
        year_text = cast(TemplateRecord.last_world_year, String)

        # Apply the collation only on MySQL/MariaDB (SQLite has no such collations).
        if self.dialect_name in ("mysql", "mariadb"):
            year_text = year_text.collate("utf8mb4_unicode_ci")

        stmt = select(TemplateRecord).where(
            TemplateRecord.last_world_file.is_not(None),
            TemplateRecord.last_world_year.is_not(None),
            TemplateRecord.last_world_file.not_like(func.concat("%", year_text, "%")),
        )
        return list(self.session.scalars(stmt).all())

    def get_template(self, template_id: int) -> TemplateRecord | None:
        return self.get_record_by_id(template_id)

    def get_template_by_title(self, title: str) -> TemplateRecord | None:
        return self.get_by(title=title)

    def add_template_data(self, data: dict[str, Any]) -> TemplateRecord | None:
        title = data.get("title", "")
        self.validate_or_raise(
            title=title.strip(),
        )
        existing = self.get_template_by_title(title)
        if existing:
            raise DuplicateRecordError(f"Template '{title}' already exists")

        data = ensure_template_data(data)

        try:
            return self.create(**data)
        except Exception as exc:
            logger.error("Failed to create new record: %s", exc)
            return None

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
