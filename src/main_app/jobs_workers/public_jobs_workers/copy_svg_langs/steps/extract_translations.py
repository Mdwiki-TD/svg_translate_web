"""
Step for extracting translations from a SVG file.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    from CopySVGTranslation import SVGTranslationExtractor  # type: ignore

    perform_svg_extract = False
except ImportError:
    from CopySVGTranslation import extract

    perform_svg_extract = True

logger = logging.getLogger(__name__)


@dataclass
class Translations:
    """Container for extracted SVG translation data."""

    new: dict[str, dict[str, str]] = field(default_factory=dict)
    tspans_by_id: dict[str, str] = field(default_factory=dict)
    title: dict[str, Any] = field(default_factory=dict)
    title_new: dict[str, Any] = field(default_factory=dict)
    error: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractResult:
    success: bool | None = None
    message: str | None = None
    error: str | None = None
    translations: dict | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def extract_file_translations(
    svg_file_path: str | Path,
) -> Translations:
    """
    Legacy function-style wrapper around SVGTranslationExtractor, kept for
    backward compatibility with existing callers.

    Parameters:
        svg_file_path (str | Path): Path to the SVG file to process.
        case_insensitive (bool): If true, treat default text keys
            case-insensitively by lowercasing them.
    """
    if perform_svg_extract:
        translations = extract(svg_file_path, case_insensitive=True)
        return Translations(**translations) if translations else Translations()

    extractor = SVGTranslationExtractor(
        svg_file_path,
        case_insensitive=True,
    )

    result = extractor.extract_file_translations()

    return result


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
        translations = extract_file_translations(main_title_path)
    except Exception:
        logger.exception("Failed to extract translations from main SVG")
        return ExtractResult(success=False, message="", error="Failed to parse main SVG", translations={})

    new_translations = translations.new
    new_translations_count = len(new_translations)

    if new_translations_count == 0:
        error = "No translations found in main file"
        logger.debug(error)
        return ExtractResult(success=False, message="", error="No translations found in main file", translations={})

    # Sort new data: alphabetical keys first, numeric keys last
    translations.new = dict(
        sorted(
            new_translations.items(),
            key=lambda item: (isinstance(item[0], str) and item[0].isdigit(), item[0]),
        )
    )
    message = f"Loaded {new_translations_count} translations from main file"

    return ExtractResult(
        success=True,
        message=message,
        error=None,
        translations=translations.to_json(),
    )


__all__ = [
    "extract_from_path",
]
