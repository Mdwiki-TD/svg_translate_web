import logging
import re
import threading
from pathlib import Path
from typing import Any, Dict

from ...config import DbConfig, settings
from ...db.task_store_pymysql import TaskStorePyMysql
from .job import CopySvgLangsProcessor

logger = logging.getLogger(__name__)


def _compute_output_dir(title: str) -> Path:
    """Return the filesystem directory used to store intermediate task output.

    Parameters:
        title (str): User-provided title for the translation task.

    Returns:
        pathlib.Path: Directory path under ``svg_data_dir`` named after a
        sanitized slug derived from ``title``. The directory is created if
        missing.
    """

    # Align with CLI behavior: store under repo svg_data/<slug>
    # Use last path segment and sanitize for filesystem safety
    name = Path(title).name
    # ---
    logger.debug(f"compute_output_dir: {name=}")
    # ---
    # name = death rate from obesity
    slug = re.sub(r"[^A-Za-z0-9._\- ]+", "_", str(name)).strip("._") or "untitled"
    slug = slug.replace(" ", "_").lower()
    # ---
    out = Path(settings.paths.svg_data) / slug
    # ---
    out.mkdir(parents=True, exist_ok=True)
    # ---
    # log title to out/title.txt
    try:
        with open(out / "title.txt", "w", encoding="utf-8") as f:
            f.write(name)
    except Exception as e:
        logger.error(f"Failed to write title to {out / 'title.txt'}: {e}")
    # ---
    return out


def make_stages():
    """
    Create an initial stages dictionary describing progress metadata for the workflow.

    Returns:
        dict: Mapping of stage names ('initialize', 'text', 'titles', 'translations', 'download', 'inject', 'upload')
        to metadata objects with the keys:
          - 'number' (int): stage order,
          - 'sub_name' (str): optional sub-stage name,
          - 'status' (str): current stage status (e.g., "Running", "Pending"),
          - 'message' (str): human-readable status message.
    """
    return {
        "initialize": {"number": 1, "sub_name": "", "status": "Running", "message": "Starting workflow"},
        "text": {"sub_name": "", "number": 2, "status": "Pending", "message": "Getting text"},
        "titles": {"sub_name": "", "number": 3, "status": "Pending", "message": "Getting titles"},
        "translations": {"sub_name": "", "number": 4, "status": "Pending", "message": "Getting translations"},
        "download": {"sub_name": "", "number": 5, "status": "Pending", "message": "Downloading files"},
        "nested": {"sub_name": "", "number": 6, "status": "Pending", "message": "Analyze nested files"},
        "inject": {"sub_name": "", "number": 7, "status": "Pending", "message": "Injecting translations"},
        "upload": {"sub_name": "", "number": 8, "status": "Pending", "message": "Uploading files"},
    }


def fail_task(
    store: TaskStorePyMysql,
    task_id: str,
    stages: Dict[str, Dict[str, Any]],
    msg: str | None = None,
):
    """
    Mark the task as failed in the provided TaskStore and log an optional error message.

    This sets the `"initialize"` stage status to `"Completed"`, persists the updated snapshot via the store, and marks the task status as `"Failed"`.

    Parameters:
        snapshot (Dict[str, Any]): Current task snapshot; must contain a `"stages"` mapping.
        msg (str | None): Optional error message to log.
    """
    stages["initialize"]["status"] = "Completed"
    store.update_stage(task_id, "initialize", stages["initialize"])
    store.update_status(task_id, "Failed")
    if msg:
        logger.error(msg)
    return None


# --- main pipeline --------------------------------------------
def run_task(
    database_data: DbConfig,
    task_id: str,
    title: str,
    args: Any,
    user_data: Dict[str, str] | None,
    *,
    cancel_event: threading.Event | None = None,
) -> None:
    """Execute the full SVG translation pipeline for a queued task using the refactored job system.

    Parameters:
        database_data (DbConfig): Database connection details for task state management.
        task_id (str): Identifier of the task being processed.
        title (str): Commons title submitted by the user.
        args: Namespace-like object returned by :func:`parse_args`.
        user_data (dict): Authentication payload used for upload operations.

    Side Effects:
        Updates task records, writes files under ``svg_data_dir``, and interacts
        with external services for downloading and uploading files.
    """
    with TaskStorePyMysql(database_data) as store:
        stages_list = make_stages()

        def sync_stages_to_db(result: dict[str, Any]):
            """Sync stages from Processor result back to the legacy task store."""
            if "stages" not in result:
                return

            for stage_name, stage_data in result["stages"].items():
                if stage_name in stages_list:
                    # Sync common fields
                    stages_list[stage_name]["status"] = stage_data.get("status", "Pending")
                    if "message" in stage_data:
                        stages_list[stage_name]["message"] = stage_data["message"]
                    store.update_stage(task_id, stage_name, stages_list[stage_name])

            # Special handling for main_file column
            if "stages" in result and "titles" in result["stages"]:
                titles_data = result["stages"]["titles"].get("data")
                if titles_data and titles_data.get("main_title"):
                    main_title = titles_data["main_title"]
                    value = f"File:{main_title}" if not main_title.lower().startswith("file:") else main_title
                    store.update_task_one_column(task_id, "main_file", value)

        store.update_status(task_id, "Running")

        # Initial data update
        task_snapshot = {"title": title}
        store.update_data(task_id, task_snapshot)

        # Initialize result object for Processor
        processor_result = {
            "status": "running",
            "stages": stages_list,
        }

        # Create the processor
        processor = CopySvgLangsProcessor(
            job_id=task_id,  # Using task_id as job_id for the processor
            title=title,
            args=args,
            user=user_data,
            result=processor_result,
            result_file=f"task_{task_id}.json",
            cancel_event=cancel_event,
        )

        # Override _save_progress to sync with legacy task store
        original_save_progress = processor._save_progress

        def wrapped_save_progress():
            original_save_progress()
            sync_stages_to_db(processor.result)

        processor._save_progress = wrapped_save_progress

        # Execute
        try:
            final_result = processor.run()

            # Final sync and result summary
            sync_stages_to_db(final_result)

            if final_result.get("results_summary"):
                store.update_results(task_id, final_result["results_summary"])

            final_status = (
                "Failed" if any(s.get("status") == "Failed" for s in stages_list.values()) else final_result["status"]
            )
            # Standardize status for legacy store
            if final_status == "completed":
                final_status = "Completed"
            elif final_status == "failed":
                final_status = "Failed"
            elif final_status == "cancelled":
                final_status = "Cancelled"

            stages_list["initialize"]["status"] = "Completed"
            store.update_stage(task_id, "initialize", stages_list["initialize"])
            store.update_status(task_id, final_status)

        except Exception as e:
            logger.exception(f"Fatal error in run_task for task {task_id}")
            fail_task(store, task_id, stages_list, str(e))
