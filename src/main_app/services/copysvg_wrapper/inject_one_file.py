"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import SVGTranslationInjector, TranslationConfig  # type: ignore
from CopySVGTranslation.exceptions import CopySVGTranslationError  # type: ignore

from .mapping import (
    InjectorData,
    InjectorStats,
    InjectResult,
    TranslationMapping,
)

logger = logging.getLogger(__name__)


def write_msg(stats: InjectorStats) -> str:

    if stats.new_languages_count > 0:
        msg = f"{stats.new_languages_count} languages injected"

    elif stats.updated_translations > 0:
        msg = f"{stats.updated_translations} translations Updated"

    elif stats.inserted_translations > 0:
        msg = f"{stats.inserted_translations} translations inserted"

    return msg


def start_svg_injection(
    *,
    inject_file: Path | str,
    mapping: dict[str, Any] | TranslationMapping | None = None,
    overwrite_translations: bool = False,
) -> InjectorData:
    """
    Legacy function-style wrapper around SVGTranslationInjector, kept for
    backward compatibility with existing callers.
    """
    config = TranslationConfig(
        case_insensitive=True,
        overwrite_translations=overwrite_translations,
        pretty_print=True,
    )

    file_name = inject_file.name if isinstance(inject_file, Path) else str(inject_file)

    injector = SVGTranslationInjector(config=config)

    try:
        data: InjectorData = injector.inject(
            svg_path=inject_file,
            mapping=mapping,
        )

    except CopySVGTranslationError as exc:
        logger.error(f"CopySVGTranslationError on file:{file_name}.")
        logger.error(f"Error code: {exc.code}")
        logger.error(f"Error label: {exc.label}")
        return InjectorData.from_error(exc)

    except Exception as exc:
        logger.error(f"Error injecting translations into {file_name}: {exc}")
        return InjectorData.from_error(exc)

    return data


def inject_step_one_file(
    file: Path,
    translations: dict[str, Any] | TranslationMapping,
    output_file: Path,
    overwrite_translations: bool = False,
) -> InjectResult:
    """Inject translations into a collection of SVG files and write the results."""
    if isinstance(translations, TranslationMapping):
        translations = translations.to_json()

    data = start_svg_injection(
        inject_file=file,
        mapping=translations,
        overwrite_translations=overwrite_translations,
    )

    stats_obj = data.inject_stats
    result_error = stats_obj.error or (data.error.code if data.error else None)
    tree = data.tree

    if not tree:
        logger.debug(f"Failed to translate {file.name}")
        msg = "Failed to translate"

        if result_error == "nested_tspan_error":
            msg = "Nested tspan error"

        return InjectResult(result=False, msg=msg)

    if result_error:
        logger.debug(f"Failed to translate {file.name}")
        return InjectResult(result=False, msg=result_error)

    if not stats_obj.has_changes():
        return InjectResult(result=None, msg="No changes")

    msg = write_msg(stats_obj)

    try:
        tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)  # type: ignore
        return InjectResult.from_stats(
            stats=stats_obj,
            result=True,
            msg=msg,
        )

    except (OSError, Exception):
        logger.error("Failed to write translated SVG: %s", output_file)
        return InjectResult.from_stats(
            stats=stats_obj,
            result=False,
            msg="Failed to write file",
        )


__all__ = [
    "InjectResult",
    "inject_step_one_file",
]
