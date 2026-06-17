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
    new_path: Optional[str] = None
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
            return InjectResult(**{"result": False, "msg": "Nested tspan error"})

        return InjectResult(**{"result": False, "msg": "Failed to translate"})

    if stats.get("error"):
        logger.debug(f"Failed to translate {file.name}")
        return InjectResult(**{"result": False, "msg": stats.get("error")})

    if stats.get("new_languages", 0) == 0 and stats.get("updated_translations", 0) == 0:
        return InjectResult(**{"result": False, "msg": "No changes"})

    try:
        tree.write(str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True)  # type: ignore
        return InjectResult(
            **{
                "result": True,
                "msg": "Injected",
                "new_path": str(output_file),
                "new_languages": stats.get("new_languages", 0),
            }
        )
    except Exception:
        return InjectResult(
            **{
                "result": False,
                "msg": "Failed to write file",
                "new_path": None,
                "new_languages": stats.get("new_languages", 0),
            }
        )


def inject_step_one_file(
    title: str,
    file_path_str: str,
    translations: dict[str, Any],
    output_dir_translated: Path,
    overwrite: bool = False,
) -> InjectResult:
    """ """
    file_path = Path(file_path_str)

    output_file = output_dir_translated / file_path.name
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
            new_path=None,
            new_languages=None,
        )

    results: dict[str, Any] = {}

    inject_files = injects_result["files"]

    file_data = inject_files.get(Path(file_path).name, {})

    if file_data.get("file_path"):
        return InjectResult(
            result=True,
            msg=f"Injected {file_data.get('new_languages', 0)} languages",
            new_path=file_data.get("file_path"),
            new_languages=file_data.get("new_languages", 0),
        )

    elif title in inject_files:
        results[title] = {
            "result": True if file_data.get("no_changes") else False,
            "msg": file_data.get("error") or "No changes",
            "new_languages": 0,
        }
    else:
        results[title] = {"result": False, "msg": "Injection failed or skipped", "new_languages": 0}

    return InjectResult(
        result=True,
        msg="Failed during SVG translation injection",
        new_path=None,
        new_languages=None,
    )
