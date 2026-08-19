from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from CopySVGTranslation import TranslationMapping  # type: ignore
from CopySVGTranslation.result import InjectorStats, InjectorData  # type: ignore

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
    mapping: ExtractorData | None = None

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_any(cls, data: dict[str, Any] | ExtractResult) -> ExtractResult:
        if isinstance(data, ExtractResult):
            return data

        translations = data.get("translations") or {}
        mapping = data.get("mapping") or ExtractorData.from_any(translations)

        return cls(
            success=data.get("success"),
            message=data.get("message"),
            error=data.get("error"),
            translations=translations,
            mapping=mapping,
        )


@dataclass
class ExtractorData:
    """
    Full mapping produced by extraction and consumed by injection.

    Attributes
    ----------
    new:
        Main map: normalized source text → {lang: translated text}
    title_new:
        Optional year-title variants advanced use
    tspans_by_id:
        Optional diagnostic map from extraction (id → default text)
    ----------
    same as TranslationMapping
    """

    new: dict[str, dict[str, str]] = field(default_factory=dict)
    title_new: dict[str, dict[str, str]] = field(default_factory=dict)
    tspans_by_id: dict[str, str] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_any(cls, data: dict[str, Any] | ExtractorData) -> ExtractorData:
        if isinstance(data, ExtractorData):
            return data

        data_json = data

        if not isinstance(data_json, dict) and not isinstance(data_json, Mapping):
            raise TypeError(f"Expected Mapping/ExtractorData/dict, got {type(data_json)}")

        # data_json = copy.deepcopy(data_json)
        return cls(
            new=dict(data_json.get("new", {})),
            title_new=dict(data_json.get("title_new", {})),
            tspans_by_id=dict(data_json.get("tspans_by_id", {})),
            meta=dict(data_json.get("meta", {})),
            error=data_json.get("error", ""),
        )

    @classmethod
    def from_extractor_data(cls, data: Mapping[str, Any]) -> ExtractorData:
        """Create from the dict currently returned by the legacy extractor."""
        return cls.from_any(data)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def is_empty(self) -> bool:
        return not self.new and not self.title_new

    def all_languages(self) -> set[str]:
        langs: set[str] = set()
        for section in (self.new, self.title_new):
            for translate in section.values():
                if isinstance(translate, dict):
                    langs.update(translate.keys())
                else:
                    raise TypeError(f"Unexpected type: {type(translate)}: section: {str(section)}")

        return langs

    def lookup(self, source: str, *, case_insensitive: bool = True) -> dict[str, str]:
        """Return {lang: text} for a source string, or empty dict."""
        key = source.lower() if case_insensitive else source

        if case_insensitive:
            for k, v in self.new.items():
                if k.lower() == key:
                    return dict(v)
            return {}

        return dict(self.new.get(key, {}))

    def entries(self) -> Iterator[TranslationEntry]:
        for source, trans in self.new.items():
            yield TranslationEntry(source=source, translations=trans)

    # ------------------------------------------------------------------
    # Mutation helpers (used while building the mapping)
    # ------------------------------------------------------------------
    def add(self, source: str, lang: str, text: str, *, case_insensitive: bool = True) -> None:
        key = source.lower() if case_insensitive else source
        self.new.setdefault(key, {})[lang] = text

    def merge(self, other: ExtractorData | Mapping[str, Any], merge_keys: list[str] | None = None) -> None:
        """
        Mapping structure to understand merge logic:
        {
            "new": { "text, 1990": { "abr": "text, afe 1990", "ar": "نص، 1990" } },
            "tspans_by_id": { "trsvg1": "text, 1990" },
            "title_new": { "text, {year}": { "abr": "text, afe {year}", "ar": "نص، {year}" } },
            "meta": {
                "header": { "text, 1990": { "abr": "text, afe 1990", "ar": "نص، 1990" } }
            },
            "error": ""
        }
        """

        def _merge_dict(self_new, other_new) -> None:
            for source, lang_dict in other_new.items():
                self_new.setdefault(source, {})
                for lang, text in lang_dict.items():
                    if lang not in self_new[source]:
                        self_new[source][lang] = text

        if merge_keys is None:
            merge_keys = ["new", "title_new", "tspans_by_id"]

        other = self.from_any(other)

        # Merge new mapping
        # new structure: {"new": { "text, 1990": { "abr": "text, afe 1990", "ar": "نص، 1990" } }, ...}
        if "new" in merge_keys:
            _merge_dict(self.new, other.new)

        # Merge title_new mapping
        # title_new structure: {"title_new": { "text, {year}": { "abr": "text, afe {year}", "ar": "نص، {year}" } }, ...}
        if "title_new" in merge_keys:
            _merge_dict(self.title_new, other.title_new)

        # Merge tspans_by_id mapping
        if "tspans_by_id" in merge_keys:
            self.tspans_by_id.update(other.tspans_by_id)

        # Should we Merge meta?

    def to_json(self) -> dict[str, Any]:
        error = self.error or self.meta.get("error") or ""
        return {
            "new": self.new,
            "title_new": self.title_new,
            "tspans_by_id": self.tspans_by_id,
            "meta": self.meta,
            "error": error,
        }


__all__ = [
    "TranslationMapping",
    "InjectorStats",
    "InjectorData",
    "InjectResult",
    "ExtractorData",
    "ExtractResult",
]
