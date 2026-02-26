"""Download task helper with progress callbacks."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable
from tqdm import tqdm

from ...config import settings
from ...db.task_store_pymysql import TaskStorePyMysql
from ...utils.commons_client import create_commons_session
from ...utils.download_file_utils import download_one_file

logger = logging.getLogger(__name__)


def download_task(
    task_id: str,
    stages: Dict[str, Any],
    output_dir_main: Path,
    titles: Iterable[str],
    store: TaskStorePyMysql | None = None,
    check_cancel: Callable[[str | None], bool] | None = None,
):
    """
    Orchestrates downloading a set of Wikimedia Commons SVGs while updating a mutable stages dict and an optional progress updater.

    Parameters:
        stages (Dict[str, str]): Mutable mapping that will be updated with "message" and "status" to reflect current progress and final outcome.
        output_dir_main (Path): Directory where downloaded files will be saved.
        titles (Iterable[str]): Iterable of file titles to download.
    Returns:
        (files, stages) (Tuple[List[str], Dict[str, str]]): `files` is the list of downloaded file paths (as strings); `stages` is the same dict passed in, updated with a final "status" of "Completed" or "Failed" and a final "message" summarizing processed and failed counts.
    """
    titles = list(titles)
    total = len(titles)

    stages["message"] = f"Downloading 0/{total:,}"
    stages["status"] = "Running"
    if store:
        store.update_stage(task_id, "download", stages)

    out_dir = Path(str(output_dir_main))
    out_dir.mkdir(parents=True, exist_ok=True)

    session = create_commons_session(settings.oauth.user_agent)

    def message_updater(value: str) -> None:
        if store:
            store.update_stage_column(task_id, "download", "stage_message", value)

    files: list[str] = []

    done = 0
    not_done = 0
    existing = 0
    not_done_list = []
    for index, title in enumerate(tqdm(titles, total=len(titles), desc="Downloading files"), 1):
        result = download_one_file(title, out_dir, index, session)
        status = result["result"] or "failed"
        if status == "success":
            done += 1
        elif status == "existing":
            existing += 1
        else:
            not_done += 1
            not_done_list.append(title)

        stages["message"] = f"Downloading {index:,}/{len(titles):,}"

        if result["path"]:
            files.append(str(result["path"]))

        stages["message"] = (
            f"Total Files: {total:,}, "
            f"Downloaded {done:,}, "
            f"skip existing {existing:,}, "
            f"failed to download: {not_done:,}"
        )
        message_updater(stages["message"])

        if index % 10 == 0:
            if check_cancel and check_cancel("download"):
                return files, stages, not_done_list

    logger.debug("files: %s", len(files))

    stages["status"] = "Failed" if not_done >= 10 else "Completed"

    logger.debug(
        "Downloaded %s files, skipped %s existing files, failed to download %s files",
        done,
        existing,
        not_done,
    )

    return files, stages, not_done_list
