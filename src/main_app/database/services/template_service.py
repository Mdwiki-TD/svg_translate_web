from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import String, cast, func, select

from ...extensions import db
from ..exceptions import DuplicateRecordError
from ..models.templates import TemplateRecord
from ..templates_utils import ensure_template_data
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class TemplateService(CRUDService[TemplateRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, TemplateRecord)

    def list(self, limit: int | None = None) -> list[TemplateRecord]:
        return super().list(
            limit=limit,
            order_by=[TemplateRecord.title],
        )

    def list_templates_mismatched_years(self) -> list[TemplateRecord]:
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

        results = self.session.scalars(stmt).all()
        return list(results)

    def get_template(self, template_id: int) -> TemplateRecord | None:
        return self.get_record_by_id(template_id)

    def get_template_by_title(self, title: str) -> TemplateRecord | None:
        return self.get_by(title=title)

    def add_template_data(self, data: dict[str, Any]) -> TemplateRecord | None:
        title = data.get("title", "")
        if not title or not title.strip():
            raise ValueError("Title is required")

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
