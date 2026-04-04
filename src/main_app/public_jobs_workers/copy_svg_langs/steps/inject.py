"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import start_injects  # type: ignore

logger = logging.getLogger(__name__)


def start_injects_wrap(files, translations, output_dir_translated, overwrite=False) -> dict[str, str | int]:
    result = start_injects(files, translations, output_dir_translated, overwrite=overwrite)

    success: int = result["success"]
    failed: int = result["failed"]
    nested_files: int = result["nested_files"]
    no_changes: int = result["no_changes"]

    result_files: dict[str, dict[str, Any]] = {
        x: {
            "file_name": x,
            "file_path": v.get("file_path", ""),
            "new_languages": v.get("new_languages", ""),
            "no_changes": v.get("no_changes", ""),
            "error": v.get("error", ""),
        }
        for x, v in result["files"].items()
    }

    return {
        "success": success,
        "failed": failed,
        "nested_files": nested_files,
        "no_changes": no_changes,
        "files": result_files,
    }


def inject_step(
    files_dict: dict[str, str],
    translations: dict[str, Any],
    output_dir: Path,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Perform translation injection on a list of SVG files.

    Args:
        files_dict: Dictionary of files to inject. key is title, value is file path.
        translations: Dictionary of translations to inject.
        output_dir: Directory where translated files should be saved.
        overwrite: Whether to overwrite existing files.

    Returns:
        dict with keys: success (bool), summary (dict), data (dict), files_to_upload (dict)
    """
    output_dir_translated = output_dir / "translated"
    output_dir_translated.mkdir(parents=True, exist_ok=True)

    files = list(files_dict.values())

    try:
        injects_result: dict[str, Any] = start_injects_wrap(
            files, translations, output_dir_translated, overwrite=overwrite
        )
    except Exception:
        logger.exception("Failed during SVG translation injection")
        return {
            "success": False,
            "summary": {
                "total": len(files_dict),
                "success": 0,
                "failed": len(files_dict),
                "no_changes": 0,
                "nested_files": 0,
            },
            "data": {},
            "files_to_upload": {},
            "results": {title: {"result": False, "msg": "Injection failed"} for title in files_dict},
            "message": "Injection failed",
        }

    success_count = injects_result.get("success") or injects_result.get("saved_done", 0)
    failed_count = injects_result.get("failed") or injects_result.get("no_save", 0)
    no_changes_count = injects_result.get("no_changes", 0)
    nested_files_count = injects_result.get("nested_files", 0)

    # Normalize keys
    injects_result["success"] = success_count
    injects_result["failed"] = failed_count

    summary = {
        "success": success_count,
        "total": len(files_dict),
        "failed": failed_count,
        "no_changes": no_changes_count,
        "nested_files": nested_files_count,
    }

    message = f"Success {success_count}/{len(files_dict)}, Failed {failed_count}, No Changes {no_changes_count}, Nested Files {nested_files_count}"
    results = {}

    inject_files = injects_result["files"]
    for title, file_path in files_dict.items():
        name = Path(file_path).name
        file_data = inject_files.get(name, {})

        if file_data.get("file_path"):
            results[title] = {
                "result": True,
                "msg": f"Injected {file_data.get('new_languages', 0)} languages",
                "new_languages": file_data.get("new_languages", 0),
            }

        elif title in inject_files:
            results[title] = {
                "result": True if file_data.get("no_changes") else False,
                "msg": file_data.get("error") or "No changes needed",
                "new_languages": 0,
            }
        else:
            results[title] = {"result": False, "msg": "Injection failed or skipped", "new_languages": 0}

    return {
        "success": success_count > 0 or len(files_dict) == 0,
        "summary": summary,
        "data": injects_result,
        "message": message,
        "results": results,
    }
