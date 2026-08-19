from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from CopySVGTranslation import TranslationMapping  # type: ignore
from CopySVGTranslation.core.mapping import InjectorData, InjectorStats  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class SharedMapToJson:
    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class InjectResult(SharedMapToJson):
    result: bool | None = None
    msg: str | None = None
    new_languages_count: int | None = None
    updated_translations: int | None = None
    inserted_translations: int | None = None

    languages_before: list[str] = field(default_factory=list)
    languages_after: list[str] = field(default_factory=list)


@dataclass
class ExtractResult(SharedMapToJson):
    success: bool | None = None
    message: str | None = None
    error: str | None = None
    translations: dict | None = None
    mapping: TranslationMapping | None = None

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_any(cls, data: dict[str, Any] | ExtractResult) -> ExtractResult:
        if isinstance(data, ExtractResult):
            return data

        translations = data.get("translations") or {}
        mapping = data.get("mapping") or TranslationMapping.from_any(translations)

        return cls(
            success=data.get("success"),
            message=data.get("message"),
            error=data.get("error"),
            translations=translations,
            mapping=mapping,
        )


__all__ = [
    "TranslationMapping",
    "InjectorStats",
    "InjectorData",
    "InjectResult",
    "TranslationMapping",
    "ExtractResult",
]
