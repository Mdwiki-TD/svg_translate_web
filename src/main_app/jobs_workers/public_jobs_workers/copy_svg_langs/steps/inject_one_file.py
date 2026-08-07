"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import SVGTranslationInjector, TranslationConfig, TranslationMapping  # type: ignore

from .mapping import (
    InjectorData,
    InjectorStats,
    InjectResult,
)

logger = logging.getLogger(__name__)


def start_svg_injection(
    *,
    inject_file: Path | str,
    mapping: dict[str, Any] | TranslationMapping | None = None,
    overwrite: bool = False,
) -> InjectorData:
    """
    Legacy function-style wrapper around SVGTranslationInjector, kept for
    backward compatibility with existing callers.
    """
    config = TranslationConfig(
        case_insensitive=True,
        overwrite=overwrite,
        pretty_print=True,
    )
    injector = SVGTranslationInjector(config=config)

    data: InjectorData | Any = injector.inject(
        svg_path=inject_file,
        mapping=mapping,
    )
    if not isinstance(data, InjectorData):
        data = InjectorData(
            tree=getattr(data, "tree", None),
            inject_stats=getattr(data, "inject_stats", InjectorStats()),
        )
    # stats = data.inject_stats.to_json()
    # return data.tree, stats

    return data


def start_injects(
    file: Path,
    translations: dict[str, Any],
    output_file: Path,
    overwrite: bool = False,
) -> InjectResult:
    """Inject translations into a collection of SVG files and write the results."""
    _stats = {
        "error": None,
        "new_languages": 0,
        "updated_translations": 0,
    }
    data = start_svg_injection(
        inject_file=file,
        mapping=translations,
        overwrite=overwrite,
    )
    stats_obj = data.inject_stats
    tree = data.tree

    if not tree:
        logger.debug(f"Failed to translate {file.name}")
        msg = "Failed to translate"

        if stats_obj.error == "nested_tspan_error" or stats_obj.nested_tspan_error:
            msg = "Nested tspan error"

        return InjectResult(result=False, msg=msg)

    languages_after = stats_obj.languages_after
    new_languages_count = stats_obj.new_languages or len(languages_after)

    inserted_translations = stats_obj.inserted_translations
    updated_translations = stats_obj.updated_translations

    if stats_obj.error:
        logger.debug(f"Failed to translate {file.name}")
        return InjectResult(result=False, msg=stats_obj.error)

    if not any((new_languages_count, updated_translations, inserted_translations)):
        return InjectResult(result=None, msg="No changes")

    if new_languages_count > 0:
        msg = f"{new_languages_count} languages injected"

    elif updated_translations > 0:
        msg = f"{updated_translations} translations Updated"

    elif inserted_translations > 0:
        msg = f"{inserted_translations} translations inserted"

    try:
        tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)  # type: ignore
        return InjectResult(
            result=True,
            msg=msg,
            languages_after=languages_after,
            new_languages_count=new_languages_count,
            updated_translations=updated_translations,
            inserted_translations=inserted_translations,
        )
    except (OSError, Exception):
        logger.error("Failed to write translated SVG: %s", output_file)
        return InjectResult(
            result=False,
            msg="Failed to write file",
            languages_after=languages_after,
            new_languages_count=new_languages_count,
            updated_translations=updated_translations,
            inserted_translations=inserted_translations,
        )


def inject_step_one_file(
    file_path: Path,
    translations: dict[str, Any],
    output_file: Path,
    overwrite: bool = False,
) -> InjectResult:
    """ """
    try:
        injects_result: InjectResult = start_injects(
            file_path,
            translations,
            output_file,
            overwrite=overwrite,
        )
    except Exception:
        logger.exception("Failed during SVG translation injection")
        return InjectResult(
            result=False,
            msg="Failed during SVG translation injection",
            new_languages_count=None,
        )

    return injects_result


__all__ = [
    "InjectResult",
    "start_injects",
    "inject_step_one_file",
]
