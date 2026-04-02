"""Step for fixing nested tags in SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from CopySVGTranslation import fix_nested_file, match_nested_tags  # type: ignore

logger = logging.getLogger(__name__)


def fix_nested_step(
    files: list[str],
    cancel_check: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    """
    Analyze and fix nested tags in a list of SVG files.

    Args:
        files: List of paths to SVG files.
        cancel_check: Optional function to check for cancellation.
        progress_callback: Optional function to report progress.

    Returns:
        dict with keys: success (bool), summary (dict), data (dict)
    """
    data = {
        "all_files": len(files),
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
    total = len(files)

    for index, file_path_str in enumerate(files, 1):
        if cancel_check and cancel_check():
            logger.info("Fix nested step cancelled")
            break

        file_path = Path(file_path_str)
        nested_tags = match_nested_tags(str(file_path))
        len_nested = len(nested_tags)

        data["len_nested_tags_before"].setdefault(len_nested, 0)
        data["len_nested_tags_before"][len_nested] += 1

        if not nested_tags:
            if progress_callback and index % 10 == 0:
                msg = f"Fixed: {fixed_count}, Not fixed: {not_fixed_count}, Nested: {nested_files_count}"
                progress_callback(index, total, msg)
            continue

        nested_files_count += 1

        # Skip if too many nested tags (threshold from original code)
        if len_nested > 10:
            data["len_nested_tags_after"].setdefault(len_nested, 0)
            data["len_nested_tags_after"][len_nested] += 1
            not_fixed_count += 1
            continue

        if fix_nested_file(file_path, file_path):
            new_nested_tags = match_nested_tags(str(file_path))
            new_len_nested = len(new_nested_tags)

            if not new_nested_tags:
                fixed_count += 1
                data["len_nested_tags_after"].setdefault(0, 0)
                data["len_nested_tags_after"][0] += 1
            else:
                data["len_nested_tags_after"].setdefault(new_len_nested, 0)
                data["len_nested_tags_after"][new_len_nested] += 1
                not_fixed_count += 1
        else:
            not_fixed_count += 1

        if progress_callback and (index == 1 or index % 10 == 0 or index == total):
            msg = f"Fixed: {fixed_count}, Not fixed: {not_fixed_count}, Nested: {nested_files_count}"
            progress_callback(index, total, msg)

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
