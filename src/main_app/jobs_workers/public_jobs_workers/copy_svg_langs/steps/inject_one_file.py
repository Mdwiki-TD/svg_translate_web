"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import SVGTranslationInjector  # type: ignore

from .inject_utils import add_translations_from_titles
from .mapping import (
    InjectorData,
    InjectorStats,
    InjectResult,
)

logger = logging.getLogger(__name__)


def start_svg_injection(
    *,
    inject_file: Path | str,
    all_mappings: dict[str, Any] | None = None,
    overwrite: bool = False,
):
    """
    Legacy function-style wrapper around SVGTranslationInjector, kept for
    backward compatibility with existing callers.
    """
    injector = SVGTranslationInjector(
        case_insensitive=True,
        overwrite=overwrite,
        pretty_print=True,
    )

    data: InjectorData | Any = injector.inject(
        inject_file=inject_file,
        all_mappings=all_mappings,
    )
    if not isinstance(data, InjectorData):
        data = InjectorData(
            tree=getattr(data, "tree", None),
            new_stats=getattr(data, "new_stats", InjectorStats()),
        )
    stats = data.new_stats.to_json()

    return data.tree, stats


def start_injects(
    file: Path,
    translations: dict,
    output_file: Path,
    overwrite: bool = False,
) -> InjectResult:
    """Inject translations into a collection of SVG files and write the results."""
    _stats = {
        "error": None,
        "nested_tspan_error": False,
        "new_languages": 0,
        "updated_translations": 0,
    }

    tree, stats = start_svg_injection(
        inject_file=file,
        all_mappings=translations,
        overwrite=overwrite,
    )

    if not tree:
        logger.debug(f"Failed to translate {file.name}")
        if stats.get("nested_tspan_error") or stats.get("error") == "nested_tspan_error":
            return InjectResult(result=False, msg="Nested tspan error")

        return InjectResult(result=False, msg="Failed to translate")

    languages_after = stats.get("languages_after") or []
    new_languages_count = stats.get("new_languages", 0) or len(languages_after)

    updated_translations = stats.get("updated_translations", 0)

    if stats.get("error"):
        logger.debug(f"Failed to translate {file.name}")
        return InjectResult(result=False, msg=stats.get("error"))

    if new_languages_count == 0 and updated_translations == 0:
        return InjectResult(result=None, msg="No changes")

    msg = f"{new_languages_count} languages injected"

    if new_languages_count == 0 and updated_translations > 0:
        msg = f"{updated_translations} translations Updated"

    try:
        tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)  # type: ignore
        return InjectResult(
            result=True,
            msg=msg,
            languages_after=languages_after,
            new_languages_count=new_languages_count,
            updated_translations=updated_translations,
        )
    except (OSError, Exception):
        logger.error("Failed to write translated SVG: %s", output_file)
        return InjectResult(
            result=False,
            msg="Failed to write file",
            languages_after=languages_after,
            new_languages_count=new_languages_count,
            updated_translations=updated_translations,
        )


def inject_step_one_file(
    file_path: Path,
    translations: dict[str, Any],
    output_file: Path,
    overwrite: bool = False,
) -> InjectResult:
    """ """
    translations = add_translations_from_titles(translations)

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
