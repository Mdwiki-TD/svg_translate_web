"""
Objects for add_lang_categories_to_owid_pages worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ...shared_objects import StandardAdminWorkerObject


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
