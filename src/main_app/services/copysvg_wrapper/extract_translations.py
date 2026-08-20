"""
Step for extracting translations from a SVG file.
"""

from __future__ import annotations

import logging
from pathlib import Path

from CopySVGTranslation import SVGTranslationService, TranslationConfig  # type: ignore
from CopySVGTranslation.exceptions import CopySVGTranslationError

from .mapping import ExtractResult, TranslationMapping

logger = logging.getLogger(__name__)


def _extract_file_translations(
    source_file: str | Path,
) -> TranslationMapping:
    """
    Function-style wrapper around SVGTranslationService.extract, kept for
    backward compatibility with existing callers.

    Parameters:
        source_file (str | Path): Path to the SVG file to process.
    """
    config = TranslationConfig(
        case_insensitive=True,
    )
    if hasattr(config, "prepare_before_extraction"):
        config.prepare_before_extraction = True

    service = SVGTranslationService(config=config)

    file_name = source_file.name if isinstance(source_file, Path) else str(source_file)

    try:
        res = service.extract(source_file)
        if res.success and res.data is not None:
            return res.data
        else:
            error_code = res.error_code or res.error or "extraction_failed"
            return TranslationMapping(error=error_code)
    except CopySVGTranslationError as exc:
        logger.error(f"CopySVGTranslationError on file:{file_name}.")
        logger.error(f"Error code: {exc.code}")
        logger.error(f"Error label: {exc.label}")

        return TranslationMapping(error=exc.code)  # , message=exc.label)
    except Exception as e:
        logger.error(f"Failed to extract translations from {file_name}: {e}")
        return TranslationMapping(error=str(e))


def extract_from_path(main_title_path: Path, fast_return_false: bool = True) -> ExtractResult:
    """
    Load SVG translations from a Wikimedia Commons main file.

    Args:
        main_title: Commons file title (e.g., "Example.svg") to download and extract translations from.
        output_dir_main: Directory where the downloaded main file is placed.

    Returns:
        dict with keys: success (bool), translations (dict), error (str|None)
    """

    mapping = _extract_file_translations(main_title_path)

    new_translations_count = len(mapping.new)

    # If there's an error in extraction, return unsuccessful result regardless of fast_return_false
    if mapping.error:
        logger.debug(f"Extraction error: {mapping.error}")
        return ExtractResult(
            success=False,
            message="Extraction failed",
            error=mapping.error,
            translations={},
            mapping=mapping,
        )

    if fast_return_false:
        if new_translations_count == 0:
            error = "No translations found in main file"
            logger.debug(error)
            return ExtractResult(
                success=False,
                message="No translations found in main file",
                error=error,
                translations={},
                mapping=mapping,
            )

    # Sort new data: alphabetical keys first, numeric keys last
    new_translations = mapping.new
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
