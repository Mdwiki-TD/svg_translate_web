"""Step for fixing nested tags in SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from CopySVGTranslation import fix_nested_file, match_nested_tags  # type: ignore

logger = logging.getLogger(__name__)


def fix_nested_step(
    files_dict: dict[str, str],
    cancel_check: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    """
    Analyze and fix nested tags in a list of SVG files.

    Args:
        files_dict:
        cancel_check: Optional function to check for cancellation.
        progress_callback: Optional function to report progress.

    Returns:
        dict with keys: success (bool), summary (dict), data (dict), results (dict)
    """
    data = {
        "all_files": len(files_dict),
        "status": {
            "len_nested_files": 0,
            "fixed": 0,
            "not_fixed": 0,
        },
        "len_nested_tags_before": {0: 0},
        "len_nested_tags_after": {0: 0},
    }

    nested_files_count = 0
    fixed_count = 0
    not_fixed_count = 0
    results: dict[str, Any] = {}
    total = len(files_dict)

    index = 0
    for index, (title, file_path_str) in enumerate(files_dict.items(), 1):
        if cancel_check and cancel_check():
            logger.info("Fix nested step cancelled")
            break

        file_path = Path(file_path_str)
        nested_tags = match_nested_tags(str(file_path))
        len_nested = len(nested_tags)

        data["len_nested_tags_before"].setdefault(len_nested, 0)
        data["len_nested_tags_before"][len_nested] += 1

        if not nested_tags:
            results[title] = {"result": None, "msg": "No nested tags found", "file_path": file_path_str}
            if progress_callback and index % 10 == 0:
                msg = f"Fixed: {fixed_count}, Not fixed: {not_fixed_count}, Nested: {nested_files_count}"
                progress_callback(index, total, msg, results)
            continue

        nested_files_count += 1

        # Skip if too many nested tags (threshold from original code)
        if len_nested > 10:
            data["len_nested_tags_after"].setdefault(len_nested, 0)
            data["len_nested_tags_after"][len_nested] += 1
            not_fixed_count += 1
            results[title] = {"result": False, "msg": f"Too many nested tags ({len_nested})", "file_path": file_path_str}
            continue

        if fix_nested_file(file_path, file_path):
            new_nested_tags = match_nested_tags(str(file_path))
            new_len_nested = len(new_nested_tags)

            if not new_nested_tags:
                fixed_count += 1
                data["len_nested_tags_after"].setdefault(0, 0)
                data["len_nested_tags_after"][0] += 1
                results[title] = {"result": True, "msg": "Fixed nested tags", "file_path": file_path_str}
            else:
                data["len_nested_tags_after"].setdefault(new_len_nested, 0)
                data["len_nested_tags_after"][new_len_nested] += 1
                not_fixed_count += 1
                results[title] = {
                    "result": False,
                    "msg": f"Could not fix all nested tags ({new_len_nested} left)",
                    "file_path": file_path_str
                }
        else:
            not_fixed_count += 1
            results[title] = {"result": False, "msg": "Failed to fix nested tags", "file_path": file_path_str}

        if progress_callback and (index == 1 or index % 10 == 0):
            msg = f"Fixed: {fixed_count}, Not fixed: {not_fixed_count}, Nested: {nested_files_count}"
            progress_callback(index, total, msg, results)

    # update last informations when step is cancelled
    if progress_callback:
        msg = f"Fixed: {fixed_count}, Not fixed: {not_fixed_count}, Nested: {nested_files_count}"
        progress_callback(index, total, msg, results)

    data["status"]["len_nested_files"] = nested_files_count
    data["status"]["fixed"] = fixed_count
    data["status"]["not_fixed"] = not_fixed_count

    summary = {
        "total": total,
        "nested": nested_files_count,
        "fixed": fixed_count,
        "not_fixed": not_fixed_count,
    }

    return {
        "success": True,
        "summary": summary,
        "data": data,
    }
