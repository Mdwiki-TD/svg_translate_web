from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ...utils.wikitext.titles_utils import match_last_world_year

logger = logging.getLogger(__name__)


@dataclass
class TemplateRecord:
    """
    CREATE TABLE `templates` (
      `id` int(11) NOT NULL AUTO_INCREMENT,
      `title` varchar(255) NOT NULL,
      `main_file` varchar(255) DEFAULT NULL,
      `last_world_file` varchar(255) DEFAULT NULL,
      `last_world_year` int(11) DEFAULT NULL,
      `slug` varchar(255) NOT NULL DEFAULT '',
      `source` varchar(255) NOT NULL DEFAULT '',
      `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
      `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
      PRIMARY KEY (`id`),
      UNIQUE KEY `title` (`title`),
      KEY `title_index` (`title`),
      KEY `main_file` (`main_file`),
      KEY `last_world_file` (`last_world_file`),
      KEY `source` (`source`),
      KEY `last_world_year` (`last_world_year`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "templates"

    id: int
    title: str
    main_file: str | None
    last_world_file: str | None
    last_world_year: int | None = None
    source: str | None = None
    slug: str | None = None
    created_at: Any | None = None
    updated_at: Any | None = None

    def __post_init__(self):
        if not self.slug and self.source and "/grapher/" in self.source:
            slug = self.source.split("/grapher/", maxsplit=1)[1].split("?")[0]
            self.slug = slug or None

        if not self.last_world_year and self.last_world_file:
            self.last_world_year = match_last_world_year(self.last_world_file)

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
