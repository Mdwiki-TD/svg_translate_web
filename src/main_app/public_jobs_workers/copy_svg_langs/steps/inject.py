"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import start_injects  # type: ignore

logger = logging.getLogger(__name__)


def start_injects_wrap(files, translations, output_dir_translated, overwrite=False) -> dict[str, str|int]:
    result = start_injects(files, translations, output_dir_translated, overwrite=overwrite)

    success: int = result["result"]
    failed: int = result["failed"]
    nested_files: int = result["nested_files"]
    no_changes: int = result["no_changes"]

    result_files: dict[str, dict[str, Any]] = {
        x: {
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
    files: list[str],
    translations: dict[str, Any],
    output_dir: Path,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Perform translation injection on a list of SVG files.

    Args:
        files: List of paths to SVG files.
        translations: Dictionary of translations to inject.
        output_dir: Directory where translated files should be saved.
        overwrite: Whether to overwrite existing files.

    Returns:
        dict with keys: success (bool), summary (dict), data (dict), files_to_upload (dict)
    """
    output_dir_translated = output_dir / "translated"
    output_dir_translated.mkdir(parents=True, exist_ok=True)

    try:
        injects_result: dict[str, Any] = start_injects_wrap(files, translations, output_dir_translated, overwrite=overwrite)
    except Exception:
        logger.exception("Failed during SVG translation injection")
        return {
            "success": False,
            "summary": {"total": len(files), "success": 0, "failed": len(files), "no_changes": 0, "nested_files": 0},
            "data": {},
            "files_to_upload": {},
            "results": {file_path: {"result": False, "msg": "Injection failed"} for file_path in files},
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
        "total": len(files),
        "failed": failed_count,
        "no_changes": no_changes_count,
        "nested_files": nested_files_count,
    }

    message = f"Success {success_count}/{len(files)}, Failed {failed_count}, No Changes {no_changes_count}, Nested Files {nested_files_count}"

    # Identify files that are ready for upload
    inject_files = injects_result.get("files", {})
    files_to_upload = {name: data for name, data in inject_files.items() if data.get("file_path")}

    return {
        "success": success_count > 0 or len(files) == 0,
        "summary": summary,
        "data": injects_result,
        "files_to_upload": files_to_upload,
        "message": message,
    }
