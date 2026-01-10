"""Main Flask views for the SVG Translate web application."""

from __future__ import annotations

import logging
import threading
import uuid
from functools import wraps
from typing import Any, Callable, Dict

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    url_for,
)
from flask.wrappers import Response
from werkzeug.datastructures import MultiDict

from ...config import settings
from ...db import TaskAlreadyExistsError
from ...db.task_store_pymysql import TaskStorePyMysql
from ...threads.task_threads import get_cancel_event, launch_task_thread
from ...users.admin_service import active_coordinators
from ...users.current import current_user, oauth_required
from ..tasks.args_utils import parse_args

TASK_STORE: TaskStorePyMysql | None = None
TASKS_LOCK = threading.Lock()

bp_tasks_managers = Blueprint("tasks_managers", __name__)
logger = logging.getLogger("svg_translate")


def _task_store() -> TaskStorePyMysql:
    global TASK_STORE
    if TASK_STORE is None:
        TASK_STORE = TaskStorePyMysql(settings.db_data)
    return TASK_STORE


def login_required_json(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that redirects anonymous users to the index page."""

    @wraps(fn)
    def wrapper(*args, **kwargs) -> Response | Any:
        if not current_user():  # and not getattr(g, "is_authenticated", False)
            flash("You must be logged in to view this page", "warning")
            return jsonify({"error": "login-required"})
        return fn(*args, **kwargs)

    return wrapper


@bp_tasks_managers.post("/tasks/<task_id>/cancel")
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

    cancel_event = get_cancel_event(task_id)
    if cancel_event:
        cancel_event.set()

    store.update_status(task_id, "Cancelled")

    flash("Task cancelled successfully.", "success")
    return redirect(url_for("tasks.task", task_id=task_id))


@bp_tasks_managers.post("/tasks/<task_id>/restart")
@oauth_required
def restart(task_id: str):
    if not task_id:
        flash("No task id provided", "warning")
        return redirect(url_for("main.index"))

    store = _task_store()
    task = store.get_task(task_id)
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
    args = parse_args(request_form)

    new_task_id = uuid.uuid4().hex

    with TASKS_LOCK:
        try:
            store.create_task(
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


__all__ = ["bp_tasks_managers"]
