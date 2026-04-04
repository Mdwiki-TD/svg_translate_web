"""Step for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import start_injects  # type: ignore

logger = logging.getLogger(__name__)


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
        dict with keys: success (bool), summary (dict), data (dict), files_to_upload (dict), results (dict)
    """
    output_dir_translated = output_dir / "translated"
    output_dir_translated.mkdir(parents=True, exist_ok=True)

    injects_result: dict[str, Any] = start_injects(files, translations, output_dir_translated, overwrite=overwrite)

    success_count = injects_result.get("success") or injects_result.get("saved_done", 0)
    failed_count = injects_result.get("failed") or injects_result.get("no_save", 0)
    no_changes_count = injects_result.get("no_changes", 0)
    nested_files_count = injects_result.get("nested_files", 0)

    # Normalize keys
    injects_result["success"] = success_count
    injects_result["failed"] = failed_count

    summary = {
        "total": len(files),
        "success": success_count,
        "failed": failed_count,
        "no_changes": no_changes_count,
        "nested_files": nested_files_count,
    }

    message = f"Success {success_count}/{len(files)}, Failed {failed_count}, No Changes {no_changes_count}, Nested Files {nested_files_count}"

    # Identify files that are ready for upload
    inject_files = injects_result.get("files", {})
    files_to_upload = {name: data for name, data in inject_files.items() if data.get("file_path")}

    # Track per-file results
    results: dict[str, Any] = {}
    for file_path_str in files:
        # file_path_str is the source file path
        # inject_files is keyed by filename (basename)
        name = Path(file_path_str).name
        file_data = inject_files.get(name, {})

        if file_data.get("file_path"):
            results[file_path_str] = {"result": True, "msg": f"Injected {file_data.get('new_languages', 0)} languages"}
        elif name in inject_files:
            results[file_path_str] = {
                "result": True if file_data.get("no_changes") else False,
                "msg": file_data.get("error") or "No changes needed",
            }
        else:
            results[file_path_str] = {"result": False, "msg": "Injection failed or skipped"}

    return {
        "success": success_count > 0 or len(files) == 0,
        "summary": summary,
        "data": injects_result,
        "files_to_upload": files_to_upload,
        "results": results,
        "message": message,
    }
