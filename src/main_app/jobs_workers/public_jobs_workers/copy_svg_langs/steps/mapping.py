from __future__ import annotations

import copy
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from lxml import etree  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class InjectorStats:
    """
    {
        "all_languages": 0,
        "new_languages": 0,
        "languages_before": [],
        "languages_after": [],
        "processed_switches": 0,
        "inserted_translations": 0,
        "skipped_translations": 0,
        "updated_translations": 0,
        "error": "",
    }"""

    all_languages: int = 0
    new_languages: int = 0

    processed_switches: int = 0
    inserted_translations: int = 0
    skipped_translations: int = 0
    updated_translations: int = 0

    languages_before: list[str] = field(default_factory=list)
    languages_after: list[str] = field(default_factory=list)
    error: str = ""
    nested_tspan_error: bool = False

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    def _update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@dataclass
class InjectorData:
    """Container for SVG data."""

    tree: etree._ElementTree | None = None
    inject_stats: InjectorStats = field(default_factory=InjectorStats)

    def to_json(self) -> dict[str, Any]:
        inject_stats = self.inject_stats.to_json()
        return {
            "tree": self.tree,
            "inject_stats": inject_stats,
            "error": inject_stats["error"],
        }


@dataclass
class InjectResult:
    result: bool | None = None
    msg: str | None = None
    new_languages_count: int | None = None
    updated_translations: int | None = None
    inserted_translations: int | None = None

    languages_before: list[str] = field(default_factory=list)
    languages_after: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractorData:
    """Container for extracted SVG translation data."""

    new: dict[str, dict[str, str]] = field(default_factory=dict)
    tspans_by_id: dict[str, str] = field(default_factory=dict)
    title_new: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_any(cls, data: dict[str, Any] | ExtractorData) -> ExtractorData:
        if isinstance(data, ExtractorData):
            return data

        data = copy.deepcopy(data)
        return cls(
            new=dict(data.get("new", {})),
            tspans_by_id=dict(data.get("tspans_by_id", {})),
            title_new=dict(data.get("title_new", {})),
            meta=dict(data.get("meta", {})),
            error=data.get("error", ""),
        )


@dataclass
class ExtractResult:
    success: bool | None = None
    message: str | None = None
    error: str | None = None
    translations: dict | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "InjectResult",
    "InjectorStats",
    "InjectorData",
    "ExtractorData",
    "ExtractResult",
]
