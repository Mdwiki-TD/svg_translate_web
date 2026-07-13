"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from CopySVGTranslation import inject

logger = logging.getLogger(__name__)


@dataclass
class InjectResult:
    result: bool | None = None
    msg: str | None = None
    new_languages: int | None = None
    updated_translations: int | None = None


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
    tree, stats = inject(
        file,
        all_mappings=translations,
        save_result=False,
        return_stats=True,
        overwrite=overwrite,
    )

    if not tree:
        logger.debug(f"Failed to translate {file.name}")
        if stats.get("nested_tspan_error"):
            return InjectResult(result=False, msg="Nested tspan error")

        return InjectResult(result=False, msg="Failed to translate")

    new_languages = stats.get("new_languages", 0)
    updated_translations = stats.get("updated_translations", 0)

    if stats.get("error"):
        logger.debug(f"Failed to translate {file.name}")
        return InjectResult(result=False, msg=stats.get("error"))

    if new_languages == 0 and updated_translations == 0:
        return InjectResult(result=None, msg="No changes")

    msg = f"{new_languages} languages injected"

    if new_languages == 0 and updated_translations > 0:
        msg = f"{updated_translations} translations Updated"

    try:
        tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)  # type: ignore
        return InjectResult(
            result=True,
            msg=msg,
            new_languages=new_languages,
            updated_translations=updated_translations,
        )
    except (OSError, Exception):
        logger.error("Failed to write translated SVG: %s", output_file)
        return InjectResult(
            result=False,
            msg="Failed to write file",
            new_languages=new_languages,
            updated_translations=updated_translations,
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
            new_languages=None,
        )

    return injects_result


__all__ = [
    "InjectResult",
    "start_injects",
    "inject_step_one_file",
]
