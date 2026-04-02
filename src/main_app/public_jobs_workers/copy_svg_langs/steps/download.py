"""Step for downloading files for copying translations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import requests

from ....api_services.utils import download_one_file

logger = logging.getLogger(__name__)


def download_step(
    titles: list[str],
    output_dir: Path,
    session: requests.Session | None = None,
    cancel_check: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    """
    Download a set of SVG files from Wikimedia Commons.

    Args:
        titles: List of file titles to download.
        output_dir: Directory where files should be saved.
        session: Optional requests session to use.
        cancel_check: Optional function to check for cancellation.
        progress_callback: Optional function to report progress.

    Returns:
        dict with keys: success (bool), files (list[str]), failed_titles (list[str]), summary (dict), results (dict)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    files: list[str] = []
    failed_titles: list[str] = []
    results: dict[str, Any] = {}
    done = 0
    skipped_existing = 0
    total = len(titles)

    for index, title in enumerate(titles, 1):
        if cancel_check and cancel_check():
            logger.info("Download step cancelled")
            break

        result = download_one_file(title, output_dir, index, session)
        status = result.get("result", "failed")

        if status == "success":
            done += 1
            files.append(str(result["path"]))
            results[title] = {"result": True, "msg": "Downloaded successfully"}
        elif status == "existing":
            skipped_existing += 1
            files.append(str(result["path"]))
            results[title] = {"result": True, "msg": "File already exists, skipped download"}
        else:
            failed_titles.append(title)
            results[title] = {"result": False, "msg": result.get("msg", "Download failed")}

        if progress_callback:
            msg = f"Downloaded {done:,}, skipped {skipped_existing:,}, failed {len(failed_titles):,}"
            progress_callback(index, total, msg)

    summary = {
        "total": total,
        "downloaded": done,
        "skipped_existing": skipped_existing,
        "failed": len(failed_titles),
    }

    return {
        "success": len(failed_titles) < 10 or total == 0,  # Arbitrary threshold from original code
        "files": files,
        "failed_titles": failed_titles,
        "summary": summary,
        "results": results,
    }
