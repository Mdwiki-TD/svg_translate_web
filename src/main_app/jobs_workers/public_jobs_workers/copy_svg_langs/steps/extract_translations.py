"""
Step for extracting translations from a SVG file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig  # type: ignore

from .mapping import ExtractorData, ExtractResult

logger = logging.getLogger(__name__)


def extract_file_translations(
    source_file: str | Path,
) -> ExtractorData:
    """
    Legacy function-style wrapper around SVGTranslationExtractor, kept for
    backward compatibility with existing callers.

    Parameters:
        source_file (str | Path): Path to the SVG file to process.
        case_insensitive (bool): If true, treat default text keys
            case-insensitively by lowercasing them.
    """
    config = TranslationConfig(
        case_insensitive=True,
    )

    extractor = SVGTranslationExtractor(config=config)

    try:
        result_json: dict[str, Any] = extractor.extract_json(source_file)
    except Exception as e:
        logger.error(f"Failed to extract translations from {source_file}: {e}")
        return ExtractorData()

    if not result_json:
        return ExtractorData()

    error = result_json.get("error", "")
    meta = result_json.get("meta", {})
    if not error and meta:
        error = meta.get("error", "")

    result = ExtractorData(
        new=result_json.get("new", {}),
        tspans_by_id=result_json.get("tspans_by_id", {}),
        title=result_json.get("title", {}),
        title_new=result_json.get("title_new", {}),
        error=error,
    )

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
