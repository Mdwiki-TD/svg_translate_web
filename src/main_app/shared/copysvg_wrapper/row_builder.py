"""Build UI rows from ExtractorData for one target language, and rebuild mapping from form rows."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from .mapping import ExtractorData

logger = logging.getLogger(__name__)


@dataclass
class TranslateRow:
    """One row in the interactive translate edit table.

    Attributes:
        source: Normalized source text (key in ExtractorData.new).
        current: Existing translation for the target language, or empty string.
        status: ``"existing"`` if a translation already exists, ``"missing"`` otherwise.
        row_index: Position index for stable HTML form field names.
    """

    source: str
    current: str
    status: Literal["existing", "missing"]
    row_index: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "current": self.current,
            "status": self.status,
            "row_index": self.row_index,
        }


def rows_for_language(
    mapping: ExtractorData,
    lang: str,
    *,
    case_insensitive: bool = True,
) -> list[TranslateRow]:
    """Build a list of edit-table rows for one target language.

    Iterates ``mapping.new`` and, for each source key, looks up the existing
    translation for *lang* (falling back to case-insensitive match).

    Args:
        mapping: Extracted translations from ``extract_from_path``.
        lang: Target language code (e.g. ``"ar"``).
        case_insensitive: Whether to try lowercase key lookup as fallback.

    Returns:
        Ordered list of ``TranslateRow`` instances.
    """
    rows: list[TranslateRow] = []

    for idx, (source, trans) in enumerate(mapping.new.items()):
        current = ""
        if isinstance(trans, dict):
            current = trans.get(lang, "")
            if not current and case_insensitive:
                # Try lowercase match on language code
                lang_lower = lang.lower()
                for k, v in trans.items():
                    if k.lower() == lang_lower:
                        current = v
                        break

        rows.append(
            TranslateRow(
                source=source,
                current=current,
                status="existing" if current else "missing",
                row_index=idx,
            )
        )

    return rows


def mapping_from_rows(
    rows: list[dict[str, str]],
    lang: str,
) -> dict[str, Any]:
    """Build an injection-ready mapping dict from submitted form rows.

    Each element in *rows* must have ``"source"`` and ``"target"`` keys.
    Empty or whitespace-only targets are skipped (no node will be created).

    Args:
        rows: List of ``{"source": ..., "target": ...}`` dicts from the form.
        lang: Target language code.

    Returns:
        A dict shaped like ``{"new": {source: {lang: text}, ...}}``
        suitable for passing to ``inject_step_one_file`` as ``translations``.
    """
    new: dict[str, dict[str, str]] = {}

    for row in rows:
        source = (row.get("source") or "").strip()
        target = (row.get("target") or "").strip()
        if not source or not target:
            continue
        new.setdefault(source, {})[lang] = target

    return {"new": new}


def summary_from_rows(rows: list[TranslateRow]) -> dict[str, int]:
    """Compute summary counts from a list of translate rows.

    Returns:
        Dict with ``total``, ``existing``, and ``missing`` counts.
    """
    existing = sum(1 for r in rows if r.status == "existing")
    return {
        "total": len(rows),
        "existing": existing,
        "missing": len(rows) - existing,
    }


__all__ = [
    "TranslateRow",
    "rows_for_language",
    "mapping_from_rows",
    "summary_from_rows",
]
