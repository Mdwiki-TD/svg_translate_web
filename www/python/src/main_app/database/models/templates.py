from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import Model
from .base import TimestampMixin

logger = logging.getLogger(__name__)


class TemplateRecord(TimestampMixin, Model):
    """
    CREATE TABLE templates (
        id int (11) NOT NULL AUTO_INCREMENT,
        title varchar(255) NOT NULL,
        main_file varchar(255) DEFAULT NULL,
        last_world_file varchar(255) DEFAULT NULL,
        last_world_year int (11) DEFAULT NULL,
        slug varchar(255) NOT NULL DEFAULT '',
        source varchar(255) NOT NULL DEFAULT '',
        created_at timestamp NOT NULL DEFAULT current_timestamp(),
        updated_at timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (id),
        UNIQUE KEY title (title),
        KEY title_index (title),
        KEY main_file (main_file),
        KEY last_world_file (last_world_file),
        KEY source (source),
        KEY last_world_year (last_world_year)
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
    """

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    main_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_world_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_world_year: Mapped[int | None] = mapped_column(nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    source: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    files: Mapped[int | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("title", name="title"),
        Index("title_index", "title"),
        Index("main_file", "main_file"),
        Index("last_world_file", "last_world_file"),
        Index("source", "source"),
        Index("last_world_year", "last_world_year"),
    )

    def validate(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("Title is required")


__all__ = [
    "TemplateRecord",
]
