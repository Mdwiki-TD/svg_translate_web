"""Explorer routes for fix_nested tasks."""

import logging
from pathlib import Path
from flask import (
    Blueprint,
    render_template,
    send_from_directory,
    abort,
    request,
    flash,
    redirect,
    url_for,
)
from ...app_routes.admin.routes import admin_required
from ...db.fix_nested_task_store import FixNestedTaskStore
from ...db.db_class import Database
from ...config import settings
from ..explorer.compare import analyze_file
from ..fix_nested.fix_utils import log_to_task
from ...routes_utils import load_auth_payload
from ...users.current import current_user
from ...tasks.uploads import upload_file, get_user_site

bp_fix_nested_explorer = Blueprint(
    "fix_nested_explorer",
    __name__,
    url_prefix="/fix_nested"
)
logger = logging.getLogger("svg_translate")


@bp_fix_nested_explorer.route("/tasks")
def list_tasks():
    """List all fix_nested tasks."""
    # Get query parameters
    status = request.args.get("status")
    username = request.args.get("username")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    # Calculate offset
    offset = (page - 1) * per_page
    show_form = False
    # Query tasks
    db = Database(settings.db_data)
    tasks = []
    try:
        db_store = FixNestedTaskStore(db)
        tasks = db_store.list_tasks(
            status=status,
            username=username,
            limit=per_page,
            offset=offset
        )

    finally:
        db.close()
    return render_template(
        "fix_nested/tasks_list.html",
        show_form=show_form,
        tasks=tasks,
        status=status,
        username=username,
        page=page,
        per_page=per_page
    )


@bp_fix_nested_explorer.route("/tasks/<task_id>")
def task_detail(task_id: str):
    """View details of a specific fix_nested task."""
    db = Database(settings.db_data)
    try:
        db_store = FixNestedTaskStore(db)
        task = db_store.get_task(task_id)

    finally:
        db.close()

    if not task:
        abort(404, description="Task not found")

    # Check if files exist
    task_dir = Path(settings.paths.fix_nested_data) / task_id
    original_file = task_dir / "original.svg"
    fixed_file = task_dir / "fixed.svg"
    metadata_file = task_dir / "metadata.json"
    log_file = task_dir / "task_log.txt"

    # Read log if exists
    log_content = None
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                log_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read log file: {e}")

    # Read metadata if exists
    metadata = None
    if metadata_file.exists():
        try:
            import json
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read metadata file: {e}")

    # Adjust filename for display
    file_name_to_link = task.get("filename", "").replace(" ", "_")
    if file_name_to_link.lower().startswith("file:"):
        file_name_to_link = file_name_to_link[5:].lstrip()

    return render_template(
        "fix_nested/task_detail.html",
        task=task,
        has_original=original_file.exists(),
        has_fixed=fixed_file.exists(),
        log_content=log_content,
        metadata=metadata,
        file_name_to_link=file_name_to_link,
    )


@bp_fix_nested_explorer.route("/tasks/<task_id>/files/<file_type>")
def serve_file(task_id: str, file_type: str):
    """Serve original or fixed file."""
    if file_type not in ["original", "fixed"]:
        abort(400, description="Invalid file type")

    filename = f"{file_type}.svg"

    task_dir = Path(settings.paths.fix_nested_data) / task_id

    if not task_dir.exists():
        abort(404, description="File not found")

    # Security check: ensure the path is within the expected directory
    file_path = (task_dir / filename).resolve()
    if not str(file_path).startswith(str(task_dir.resolve())):
        abort(403, description="Access denied")

    return send_from_directory(str(task_dir.absolute()), filename)


@bp_fix_nested_explorer.route("/tasks/<task_id>/log")
@admin_required
def view_log(task_id: str):
    """View task log file."""
    task_dir = Path(settings.paths.fix_nested_data) / task_id
    log_file = task_dir / "task_log.txt"

    if not log_file.exists():
        abort(404, description="Log file not found")

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.read()

        from flask import Response
        return Response(log_content, mimetype="text/plain")
    except Exception as e:
        logger.error(f"Failed to read log file: {e}")
        abort(500, description="Failed to read log file")


@bp_fix_nested_explorer.route("/tasks/<task_id>/compare")
def compare(task_id: str):
    """Compare original and fixed files."""
    db = Database(settings.db_data)
    task = None
    try:
        db_store = FixNestedTaskStore(db)
        task = db_store.get_task(task_id)

    finally:
        db.close()

    if not task:
        # abort(404, description="Task not found")
        # return to HTTP_REFERER with flash message

        flash("Task not found", "danger")
        return redirect(request.referrer or url_for("fix_nested_explorer.list_tasks"))

    task_dir = Path(settings.paths.fix_nested_data) / task_id
    original_file = task_dir / "original.svg"
    fixed_file = task_dir / "fixed.svg"

    if not original_file.exists() or not fixed_file.exists():
        # abort(404, description="Original or fixed file not found")
        flash("Original or fixed file not found", "danger")
        return redirect(request.referrer or url_for("fix_nested_explorer.list_tasks"))

        # Analyze both files
    original_result = analyze_file(original_file)
    fixed_result = analyze_file(fixed_file)

    # Add nested tag counts
    from CopySVGTranslation import match_nested_tags  # type: ignore
    original_result["nested_tags_count"] = len(match_nested_tags(str(original_file)))
    fixed_result["nested_tags_count"] = len(match_nested_tags(str(fixed_file)))

    # Add file sizes
    original_result["file_size"] = original_file.stat().st_size
    fixed_result["file_size"] = fixed_file.stat().st_size

    return render_template(
        "fix_nested/compare.html",
        task=task,
        task_id=task_id,
        filename=task.get("filename", ""),
        original_result=original_result,
        fixed_result=fixed_result
    )


@bp_fix_nested_explorer.route("/tasks/<task_id>/undo", methods=["POST"])
@admin_required
def undo_task(task_id: str):
    """Undo a completed task and restore the original file."""

    # ------------------------------------------------------------------
    # 1. Authentication
    # ------------------------------------------------------------------
    current_user_obj = current_user()
    if not current_user_obj:
        flash("You must be logged in to undo tasks", "danger")
        return redirect(url_for("auth.login"))

    auth_payload = load_auth_payload(current_user_obj)
    site = get_user_site(auth_payload)
    if not site:
        flash("Failed to authenticate with Wikimedia Commons", "danger")
        return redirect(url_for("fix_nested_explorer.task_detail", task_id=task_id))

    # ------------------------------------------------------------------
    # 2. Filesystem validation
    # ------------------------------------------------------------------
    task_dir = Path(settings.paths.fix_nested_data) / task_id
    original_file = task_dir / "original.svg"

    if not original_file.exists():
        flash("Original file not found", "danger")
        return redirect(url_for("fix_nested_explorer.task_detail", task_id=task_id))

    # ------------------------------------------------------------------
    # 3. Load & validate task (DB scope is minimal)
    # ------------------------------------------------------------------
    with Database(settings.db_data) as db:
        db_store = FixNestedTaskStore(db)
        task = db_store.get_task(task_id)

    if not task:
        flash("Task not found", "danger")
        return redirect(url_for("fix_nested_explorer.list_tasks"))

    if task["status"] != "completed":
        flash("Can only undo completed tasks", "warning")
        return redirect(url_for("fix_nested_explorer.task_detail", task_id=task_id))

    if task.get("upload_result") != "Success":
        flash("Can only undo tasks with successful uploads", "warning")
        return redirect(url_for("fix_nested_explorer.task_detail", task_id=task_id))

    # ------------------------------------------------------------------
    # 4. External side effect (Commons upload)
    # ------------------------------------------------------------------
    logger.info(f"Undoing task {task_id}: Uploading original file {task['filename']}")

    upload_result = upload_file(
        file_name=task["filename"],
        file_path=original_file,
        site=site,
        summary=f"Restoring original file (undo fix_nested task {task_id[:8]})",
    )

    if not upload_result:
        flash("Failed to upload original file", "danger")
        return redirect(url_for("fix_nested_explorer.task_detail", task_id=task_id))

    # ------------------------------------------------------------------
    # 5. Persist undo result
    # ------------------------------------------------------------------
    with Database(settings.db_data) as db:
        db_store = FixNestedTaskStore(db)
        db_store.update_status(task_id, "undone")

    # Log the undo operation
    log_to_task(task_dir, f"Task undone: Original file restored by {current_user_obj.get('username', 'unknown')}")
    log_to_task(task_dir, f"Undo upload result: {upload_result}")

    flash(f"Successfully restored original file: {task['filename']}", "success")
    logger.info(f"Task {task_id} undone successfully")

    return redirect(url_for("fix_nested_explorer.task_detail", task_id=task_id))


__all__ = ["bp_fix_nested_explorer"]
