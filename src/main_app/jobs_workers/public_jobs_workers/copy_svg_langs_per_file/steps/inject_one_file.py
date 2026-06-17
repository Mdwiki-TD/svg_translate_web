"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from CopySVGTranslation import inject

logger = logging.getLogger(__name__)


@dataclass
class InjectResult:
    result: Optional[bool] = None
    msg: Optional[str] = None
    new_languages: Optional[int] = None


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
    if stats.get("error"):
        logger.debug(f"Failed to translate {file.name}")
        return InjectResult(result=False, msg=stats.get("error"))

    if new_languages == 0 and stats.get("updated_translations", 0) == 0:
        return InjectResult(result=None, msg="No changes")

    try:
        tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)  # type: ignore
        return InjectResult(
            result=True,
            msg=f"Injected {new_languages} languages",
            new_languages=new_languages,
        )
    except Exception:
        return InjectResult(
            result=False,
            msg="Failed to write file",
            new_languages=new_languages,
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
