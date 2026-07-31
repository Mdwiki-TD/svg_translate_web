"""
Step for extracting translations from a SVG file.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from CopySVGTranslation import extract  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ExtractResult:
    success: bool | None = None
    message: str | None = None
    error: str | None = None
    translations: dict | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def extract_from_path(main_title_path: Path) -> ExtractResult:
    """
    Load SVG translations from a Wikimedia Commons main file.

    Args:
        main_title: Commons file title (e.g., "Example.svg") to download and extract translations from.
        output_dir_main: Directory where the downloaded main file is placed.

    Returns:
        dict with keys: success (bool), translations (dict), error (str|None)
    """

    try:
        translations = extract(main_title_path, case_insensitive=True)
    except Exception:
        logger.exception("Failed to extract translations from main SVG")
        return ExtractResult(success=False, message="", error="Failed to parse main SVG", translations={})
    translations = translations or {}

    new_translations = translations.get("new") or {}
    new_translations_count = len(new_translations)

    if new_translations_count == 0:
        error = "No translations found in main file"
        logger.debug(error)
        return ExtractResult(success=False, message="", error="No translations found in main file", translations={})

    # Sort new data: alphabetical keys first, numeric keys last
    translations["new"] = dict(
        sorted(
            new_translations.items(),
            key=lambda item: (isinstance(item[0], str) and item[0].isdigit(), item[0]),
        )
    )
    message = f"Loaded {new_translations_count} translations from main file"

    return ExtractResult(success=True, message=message, error=None, translations=translations)


__all__ = [
    "extract_from_path",
]
