"""
Step for extracting translations from a SVG file.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import SVGTranslationExtractor, TranslationConfig  # type: ignore
from CopySVGTranslation.exceptions import CopySVGTranslationError

from .mapping import ExtractorData, ExtractResult

logger = logging.getLogger(__name__)


def _extract_file_translations(
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
    if hasattr(config, "prepare_before_extraction"):
        config.prepare_before_extraction = True

    extractor = SVGTranslationExtractor(config=config)

    file_name = source_file.name if isinstance(source_file, Path) else str(source_file)

    try:
        result_json: dict[str, Any] = extractor.extract_json(source_file)
    except CopySVGTranslationError as exc:
        logger.error(f"CopySVGTranslationError on file:{file_name}. code: {exc.code}")
        return ExtractorData(error=str(exc))
    except Exception as e:
        logger.error(f"Failed to extract translations from {file_name}: {e}")
        return ExtractorData(error=str(e))

    if not result_json:
        return ExtractorData()

    error = result_json.get("error", "")
    meta = result_json.get("meta", {})
    if not error and meta:
        error = meta.get("error", "")

    result = ExtractorData.from_any(result_json)

    if error and not result.error:
        result.error = error

    return result


def extract_from_path(main_title_path: Path, fast_return_false: bool = True) -> ExtractResult:
    """
    Load SVG translations from a Wikimedia Commons main file.

    Args:
        main_title: Commons file title (e.g., "Example.svg") to download and extract translations from.
        output_dir_main: Directory where the downloaded main file is placed.

    Returns:
        dict with keys: success (bool), translations (dict), error (str|None)
    """

    try:
        mapping = _extract_file_translations(main_title_path)
    except Exception:
        logger.exception("Failed to extract translations from main SVG")
        return ExtractResult(
            success=False,
            message="",
            error="Failed to parse main SVG",
            translations={},
            mapping=ExtractorData(),
        )

    new_translations = mapping.new
    new_translations_count = len(new_translations)

    if fast_return_false:
        if new_translations_count == 0:
            error = "No translations found in main file"
            logger.debug(error)
            return ExtractResult(
                success=False,
                message="",
                error=mapping.error or "No translations found in main file",
                translations={},
                mapping=mapping,
            )

    # Sort new data: alphabetical keys first, numeric keys last
    if new_translations:
        mapping.new = dict(
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
        translations=mapping.to_json(),
        mapping=mapping,
    )


__all__ = [
    "extract_from_path",
]
