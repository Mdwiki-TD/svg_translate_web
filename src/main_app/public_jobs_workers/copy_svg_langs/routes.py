"""Routes for copying SVG languages (translations)."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from ...app_routes.utils.routes_utils import format_task, get_error_message, order_stages
from ...services.copy_svg_langs_service import (
    _task_store,
    get_db_tasks,
)
from ...services.users_service import current_user

bp_copy_svg_langs = Blueprint("copy_svg_langs", __name__)
logger = logging.getLogger(__name__)


def format_task_message(formatted):
    for v in formatted:
        if v.get("stages"):
            for s in v["stages"]:
                v["stages"][s]["message"] = "<br>".join(v["stages"][s]["message"].split(","))
    return formatted


def load_state_hash(
    task: Optional[Dict[str, Any]],
    stages: List[tuple[str, Dict[str, Any]]],
) -> tuple[int, str]:

    # Auto-refresh tracking: get refresh count and previous state hash from query params
    refresh_count = request.args.get("refresh_count", 0, type=int)
    prev_state_hash = request.args.get("state_hash", "")
    state_payload = {
        "task_status": task.get("status", "") if isinstance(task, dict) else "",
        "task_updated_at": task.get("updated_at", "") if isinstance(task, dict) else "",
        "stages": [
            {
                "name": name,
                "status": stage.get("status", ""),
                "message": stage.get("message", ""),
                "sub_name": stage.get("sub_name", ""),
                "updated_at": stage.get("updated_at", ""),
            }
            for name, stage in stages
        ],
    }
    current_state_hash = hashlib.sha256(json.dumps(state_payload, sort_keys=True, default=str).encode()).hexdigest()[:8]
    refresh_count = 0 if current_state_hash != prev_state_hash else refresh_count + 1
    return refresh_count, current_state_hash


@bp_copy_svg_langs.get("/tasks")
@bp_copy_svg_langs.get("/tasks/user/<user>")
def tasks(user: str | None = None):
    """
    Render the task listing page with formatted task metadata and available status filters.

    Retrieve tasks from the global task store, optionally filter by status, and produce a list of task dictionaries with selected fields and display/sortable timestamp values. Also collect the distinct task statuses found and pass the tasks, the current status filter, and the sorted available statuses to the "tasks.html" template.

    Returns:
        A Flask response object rendering "tasks.html" with the context keys `tasks`, and `available_statuses`.
    """

    # Get username from query parameter, default to current user
    # user = request.args.get("user", "")
    current_user_obj = current_user()

    db_tasks = get_db_tasks(user)

    formatted = [format_task(task) for task in db_tasks]
    formatted = format_task_message(formatted)

    available_statuses = sorted({task.get("status", "") for task in db_tasks if task.get("status")})

    # Determine if viewing own tasks or another user's tasks
    is_own_tasks = current_user_obj and user == current_user_obj.username

    return render_template(
        "tasks.html",
        tasks=formatted,
        available_statuses=available_statuses,
        current_user=current_user_obj,
        tasks_user=user,
        is_own_tasks=is_own_tasks,
        user_specific=True,
    )


@bp_copy_svg_langs.get("/tasks/<task_id>")
@bp_copy_svg_langs.get("/tasks/<task_id>/info")
def task_infos(task_id: str | None = None):
    if not task_id:
        flash("No task id provided", "warning")
        return redirect(url_for("main.index"))

    task: Optional[Dict[str, Any]] = _task_store().get_task(task_id)

    if not task:
        task = {"error": "not-found"}
        logger.debug(f"Task {task_id} not found!!")

    title = request.args.get("title")
    error_message = get_error_message(request.args.get("error"))

    if error_message:
        flash(error_message, "warning")

    stages = order_stages(task.get("stages") if isinstance(task, dict) else None)

    refresh_count, current_state_hash = load_state_hash(task, stages)

    current_user_obj = current_user()
    return render_template(
        "task.html",
        task_id=task_id,
        current_user=current_user_obj,
        title=title or task.get("title", "") if isinstance(task, dict) else "",
        task=task,
        stages=stages,
        form=task.get("form", {}),
        refresh_count=refresh_count,
        state_hash=current_state_hash,
    )


@bp_copy_svg_langs.get("/status/<task_id>")
def status(task_id: str):
    """
    Return the JSON representation of the task identified by `task_id`.

    Parameters:
        task_id (str): Identifier of the task to retrieve.

    Returns:
        A JSON response containing the task data when found. If no task exists for `task_id`, a JSON error `{"error": "not-found"}` is returned with HTTP status 404.
    """
    if not task_id:
        logger.error("No task_id provided in status request.")
        return jsonify({"error": "no-task-id"}), 400

    task = _task_store().get_task(task_id)
    if not task:
        logger.debug(f"Task {task_id} not found")
        return jsonify({"error": "not-found"}), 404

    return jsonify(task)


bp_tasks = bp_copy_svg_langs
