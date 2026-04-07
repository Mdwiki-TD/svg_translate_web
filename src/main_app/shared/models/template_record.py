from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ...utils.wikitext.titles_utils import match_last_world_year

logger = logging.getLogger(__name__)


@dataclass
class TemplateRecord:
    """Representation of a template."""

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
