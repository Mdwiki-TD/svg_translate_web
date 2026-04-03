"""Step for uploading translated SVG files to Wikimedia Commons."""

from __future__ import annotations

import logging
from typing import Any, Callable

import mwclient

from ....config import Settings
from ....api_services.upload_bot import upload_file

logger = logging.getLogger(__name__)


def upload_step(
    files_to_upload: dict[str, dict[str, Any]],
    main_title: str,
    site: mwclient.Site,
    cancel_check: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> dict[str, Any]:
    """
    Upload translated SVG files to Wikimedia Commons.

    Args:
        files_to_upload: Dictionary mapping filenames to their data (including file_path).
        main_title: The title of the main file these translations came from.
        site: Authenticated mwclient.Site object.
        cancel_check: Optional function to check for cancellation.
        progress_callback: Optional function to report progress.

    Returns:
        dict with keys: success (bool), summary (dict), errors (list), results (dict)
    """
    done = 0
    not_done = 0
    no_changes = 0
    errors = []
    results: dict[str, Any] = {}

    total_files = len(files_to_upload)
    to_work = {name: data for name, data in files_to_upload.items() if data.get("new_languages")}

    # Initialize results for those not needing work
    for name in files_to_upload:
        if name not in to_work:
            results[name] = {"result": None, "msg": "No new languages to upload"}
            no_changes += 1

    main_title_link = f"[[:File:{main_title}]]" if not main_title.startswith("File:") else f"[[:{main_title}]]"

    _upload_limit = int(Settings.dynamic.get("copy_svg_langs_upload_limit", 0))

    for index, (file_name, file_data) in enumerate(to_work.items(), 1):
        if cancel_check and cancel_check():
            logger.info("Upload step cancelled")
            break

        file_path = file_data.get("file_path")
        summary = (
            f"Adding {file_data.get('new_languages')} languages translations from {main_title_link}"
            if "new_languages" in file_data
            else f"Adding translations from {main_title_link}"
        )

        if _upload_limit > 0 and index > _upload_limit:
            logger.info(f"Reached upload limit of {_upload_limit}")
            results[file_name] = {"result": None, "msg": "Reached upload limit"}
            continue

        try:
            upload_result = upload_file(file_name, file_path, site=site, summary=summary) or {}
            result_status = upload_result.get("result", "")

            if result_status == "Success":
                done += 1
                results[file_name] = {"result": True, "msg": "Uploaded successfully"}
            elif result_status == "fileexists-no-change":
                no_changes += 1
                results[file_name] = {"result": True, "msg": "File already exists with same content"}
            else:
                not_done += 1
                err_msg = upload_result.get("error", "Unknown upload error")
                results[file_name] = {"result": False, "msg": err_msg}
                if "error" in upload_result:
                    errors.append(f"{file_name}: {err_msg}")

        except Exception as e:
            logger.exception(f"Exception uploading {file_name}")
            not_done += 1
            results[file_name] = {"result": False, "msg": str(e)}
            errors.append(f"{file_name}: {str(e)}")

        if progress_callback and (index == 1 or index % 10 == 0 or index == len(to_work)):
            msg = f"Uploaded {done}, no changes: {no_changes}, failed: {not_done}"
            progress_callback(index, len(to_work), msg)

    summary = {
        "total": total_files,
        "uploaded": done,
        "no_changes": no_changes,
        "failed": not_done,
    }

    return {
        "success": not_done < 10 or total_files == 0,
        "summary": summary,
        "errors": errors,
        "results": results,
    }
