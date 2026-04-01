"""Main Flask views for the SVG Translate web application."""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
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
from werkzeug.datastructures import MultiDict

from ..admin.admins_required import admin_required
from ...config import settings
from ...db.exceptions import TaskAlreadyExistsError
from ...public_jobs_workers.copy_svg_langs.task_threads import get_cancel_event, launch_task_thread
from ...services.admin_service import active_coordinators
from ...services.copy_svg_langs_service import (
    _task_store,
    create_new_task,
    get_active_task_by_title,
    get_db_tasks,
    get_store_task,
)
from ...services.users_service import current_user, oauth_required
from ..utils.args_utils import parse_args
from ..utils.routes_utils import format_task, get_error_message, load_auth_payload, order_stages

bp_tasks = Blueprint("tasks", __name__)
logger = logging.getLogger(__name__)


def get_disable_uploads() -> str:
    return settings.disable_uploads


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


@bp_tasks.get("/task")
@bp_tasks.get("/task/<task_id>")
def task(task_id: str | None = None):
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


@bp_tasks.get("/status/<task_id>")
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


@bp_tasks.get("/tasks")
@bp_tasks.get("/tasks/<user>")
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


@bp_tasks.post("/")
@oauth_required
def start():
    user = current_user()
    title = request.form.get("title", "").strip()
    if not title:
        return redirect(url_for("main.index"))

    task_id = uuid.uuid4().hex

    args = parse_args(request.form, get_disable_uploads())

    logger.info(f"ignore_existing_task: {args.ignore_existing_task}")
    if not args.ignore_existing_task:
        existing_task = get_active_task_by_title(title)
        if existing_task:
            logger.debug(f"Task for title '{title}' already exists: {existing_task['id']}.")
            flash(f"Task for title '{title}' already exists: {existing_task['id']}.", "warning")
            return redirect(url_for("tasks.task", task_id=existing_task["id"], title=title))

    try:
        create_new_task(task_id, title, username=(user.username if user else ""), form=request.form.to_dict(flat=True))
    except TaskAlreadyExistsError as exc:
        existing = exc.task
        logger.debug("Task creation for %s blocked by existing task %s", task_id, existing.get("id"))
        flash(f"Task for title '{title}' already exists: {existing['id']}.", "warning")
        return redirect(url_for("tasks.task", task_id=existing["id"], title=title))
    except Exception:
        logger.exception("Failed to create task")
        flash("Failed to create task.", "danger")
        return redirect(url_for("main.index", title=title))

    auth_payload = load_auth_payload(user)

    launch_task_thread(task_id, title, args, auth_payload)

    return redirect(url_for("tasks.task", title=title, task_id=task_id))


@bp_tasks.post("/task/<task_id>/delete")
@admin_required
def delete_task(task_id: str):
    """Delete task."""
    try:
        _task_store().delete_task(task_id)
    except LookupError as exc:
        logger.exception("Unable to delete task.")
        flash(str(exc), "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to delete task.")
        flash("Unable to delete task. Please try again.", "danger")
    else:
        flash(f"Task '{task_id}' removed.", "success")

    return redirect(url_for("tasks.tasks"))


@bp_tasks.post("/tasks/<task_id>/cancel")
@oauth_required
def cancel(task_id: str):
    if not task_id:
        flash("No task id provided", "warning")
        return redirect(url_for("main.index"))

    store = _task_store()
    task = store.get_task(task_id)
    if not task:
        logger.debug("Cancel requested for missing task %s", task_id)
        flash(f"Task {task_id} not found", "danger")
        return redirect(url_for("main.index"))

    if task.get("status") in ("Completed", "Failed", "Cancelled"):
        flash(f"Task is already {task.get('status')}", "info")
        return redirect(url_for("tasks.task", task_id=task_id))

    user = current_user()
    if not user:
        logger.error("Cancel requested without authenticated user for task %s", task_id)
        flash("You must be logged in to cancel a task", "warning")
        return redirect(url_for("auth.login"))

    task_username = task.get("username", "")

    if task_username != user.username and user.username not in active_coordinators():
        logger.error(
            "Cancel requested for task %s by user %s, but task is owned by %s",
            task_id,
            user.username,
            task_username,
        )
        flash("You don't own this task", "danger")
        return redirect(url_for("tasks.task", task_id=task_id))

    cancel_event = get_cancel_event(task_id, store=store)
    if cancel_event:
        cancel_event.set()

    store.update_status(task_id, "Cancelled")

    flash("Task cancelled successfully.", "success")
    return redirect(url_for("tasks.task", task_id=task_id))


@bp_tasks.post("/tasks/<task_id>/restart")
@oauth_required
def restart(task_id: str):
    if not task_id:
        flash("No task id provided", "warning")
        return redirect(url_for("main.index"))

    task = get_store_task(task_id)
    if not task:
        logger.debug("Restart requested for missing task %s", task_id)
        flash(f"Task {task_id} not found", "danger")
        return redirect(url_for("main.index"))

    title = task.get("title")
    if not title:
        logger.error("Task %s has no title to restart", task_id)
        flash("Task has no title to restart", "danger")
        return redirect(url_for("tasks.task", task_id=task_id))

    user = current_user()
    if not user:
        logger.error("Restart requested without authenticated user for task %s", task_id)
        flash("You must be logged in to restart a task", "warning")
        return redirect(url_for("auth.login"))

    user_payload: Dict[str, Any] = {
        "id": user.user_id,
        "username": user.username,
        "access_token": user.access_token,
        "access_secret": user.access_secret,
    }

    stored_form = dict(task.get("form") or {})
    request_form = MultiDict(stored_form.items()) if stored_form else MultiDict()
    args = parse_args(request_form, get_disable_uploads())

    new_task_id = uuid.uuid4().hex

    try:
        create_new_task(
            new_task_id,
            title,
            username=user.username,
            form=stored_form,
        )
    except TaskAlreadyExistsError as exc:
        existing = exc.task
        logger.debug("Restart for %s blocked by existing task %s", task_id, existing.get("id"))
        flash(f"Task for title '{title}' already exists: {existing.get('id')}.", "warning")
        return redirect(url_for("tasks.task", task_id=existing.get("id")))
    except Exception:
        logger.exception("Failed to restart task %s", task_id)
        flash("Failed to restart task.", "danger")
        return redirect(url_for("tasks.task", task_id=task_id))

    launch_task_thread(new_task_id, title, args, user_payload)

    return redirect(url_for("tasks.task", task_id=new_task_id))
