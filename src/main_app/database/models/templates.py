from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import String, text
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import db
from .base import TimestampMixin

logger = logging.getLogger(__name__)


class TemplateRecord(TimestampMixin, db.Model):
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
    title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    main_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_world_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_world_year: Mapped[int | None] = mapped_column(nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    source: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    files: Mapped[int | None] = mapped_column(nullable=True)

    def __init__(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_json(self) -> dict[str, Any]:
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
            "files": self.files,
        }

    def validate(self) -> None:
        if not self.title or not self.title.strip():
            raise ValueError("Title is required")

    def extract_slug(self) -> str | None:
        """
        Extracts the chart slug from a given Our World in Data URL.

        This function looks specifically for standard grapher URLs and extracts the unique identifier (slug) of the chart,
        ignoring query parameters. If the URL is not a standard grapher link (e.g., explorer links) or is invalid,
        it returns None.

        Args:
            chart_url (str | None): The full URL string of the chart.

        Returns:
            str | None: The extracted slug string if found, otherwise None.

        Examples:
            >>> template.extract_slug("https://ourworldindata.org/grapher/death-rate-by-source-from-indoor-air-pollution?tab=map")
            'death-rate-by-source-from-indoor-air-pollution'

            >>> template.extract_slug("https://ourworldindata.org/explorers/democracy?v=1&csvType=full")
            None
        """
        if not self.source:
            return None

        # Remove query parameters from the URL
        chart_url = str(self.source).split("?")[0]

        slug = None
        # Check if it's a valid grapher URL and extract the slug
        if "/grapher/" in chart_url:
            slug = chart_url.split("/grapher/", maxsplit=1)[1]

        return slug


__all__ = [
    "TemplateRecord",
]
