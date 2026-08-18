"""
Objects for add_lang_categories_to_owid_pages worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ...shared_objects import STATUS_LITERAL, StandardAdminWorkerObject


@dataclass
class PageInfo:
    """Holds all state for a single OWID page being processed."""

    page_title: str
    svg_file: str | None = None
    lang_codes: list[str] = field(default_factory=list)
    categories_added: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: STATUS_LITERAL = "pending"
    error: str | None = None
    steps: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "load_page_text": {"result": None, "msg": ""},
            "extract_file_name": {"result": None, "msg": ""},
            "get_languages": {"result": None, "msg": ""},
            "build_categories": {"result": None, "msg": ""},
            "check_existing": {"result": None, "msg": ""},
            "save_page": {"result": None, "msg": ""},
        }
    )

    # Internal temporary state
    _text: str | None = None
    _categories: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_title": self.page_title,
            "svg_file": self.svg_file,
            "lang_codes": self.lang_codes,
            "categories_added": self.categories_added,
            "timestamp": self.timestamp,
            "status": self.status,
            "error": self.error,
            "steps": self.steps,
        }


@dataclass
class AddLangCategoriesSummary:
    total: int = 0
    processed: int = 0
    success: int = 0
    skipped: int = 0
    failed: int = 0
    no_file: int = 0


@dataclass
class AddLangCategoriesWorkerObject(StandardAdminWorkerObject):
    summary: AddLangCategoriesSummary = field(default_factory=AddLangCategoriesSummary)


__all__ = [
    "AddLangCategoriesWorkerObject",
    "AddLangCategoriesSummary",
]
