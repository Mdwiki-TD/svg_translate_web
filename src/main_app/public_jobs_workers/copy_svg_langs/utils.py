"""Utilities for the copy SVG languages job."""

from __future__ import annotations

import html
import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote

logger = logging.getLogger(__name__)


def json_save(path: Path | str, data: Any) -> None:
    """Save data to a JSON file."""
    if not data:
        logger.error(f"Empty data to save to: {path}")
        return

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.exception(f"Error saving json: {e}, path: {path}")


def commons_link(title: str, name: str | None = None) -> str:
    """Return an HTML anchor pointing to a Commons file page."""
    safe_name = html.escape(name or title, quote=True)
    href = f"https://commons.wikimedia.org/wiki/{quote(title, safe='/:()')}"
    return f"<a href='{href}' target='_blank' rel='noopener noreferrer'>{safe_name}</a>"


def make_results_summary(
    total_files: int,
    files_to_upload_count: int,
    no_file_path: int,
    injects_result: dict[str, Any],
    translations: dict[str, Any],
    main_title: str,
    upload_result: dict[str, Any],
) -> dict[str, Any]:
    """Compile the final task result payload."""
    return {
        "total_files": total_files,
        "files_to_upload_count": files_to_upload_count,
        "no_file_path": no_file_path,
        "injects_result": {
            "nested_files": injects_result.get("nested_files", 0),
            "success": injects_result.get("success", 0),
            "failed": injects_result.get("failed", 0),
        },
        "new_translations_count": len(translations.get("new", {})),
        "upload_result": upload_result,
        "main_title": main_title,
    }
