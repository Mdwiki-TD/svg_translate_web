from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import db

logger = logging.getLogger(__name__)


class TemplateRecord(db.Model):
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
    ) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_general_ci;
    """

    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    main_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_world_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_world_year: Mapped[int | None] = mapped_column(nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    source: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.current_timestamp())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "main_file": self.main_file,
            "last_world_file": self.last_world_file,
            "last_world_year": self.last_world_year,
            "source": self.source,
            "slug": self.slug,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


__all__ = [
    "TemplateRecord",
]
