
import logging
import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for

from ...routes_utils import load_auth_payload
from .fix_utils import process_fix_nested
from ...users.current import current_user, oauth_required
from ...db.fix_nested_task_store import FixNestedTaskStore
from ...db.db_class import Database
from ...config import settings

bp_fix_nested = Blueprint("fix_nested", __name__, url_prefix="/fix_nested")
logger = logging.getLogger("svg_translate")


@bp_fix_nested.route("/", methods=["GET"])
# @oauth_required
def fix_nested():
    return render_template("fix_nested/form.html")


@bp_fix_nested.route("/", methods=["POST"])
@oauth_required
def fix_nested_post():

    # POST logic
    filename = request.form.get("filename", "").strip()

    # Remove "File:" prefix if present
    if filename.lower().startswith("file:"):
        filename = filename = filename[5:].lstrip()

    if not filename:
        flash("Please provide a file name", "danger")
        return redirect(url_for("fix_nested.fix_nested"))

    # Generate unique task ID
    task_id = str(uuid.uuid4())
    logger.info(f"Starting fix_nested task {task_id} for file: {filename}")

    current_user_obj = current_user()
    auth_payload = load_auth_payload(current_user_obj)
    username = current_user_obj.get("username") if current_user_obj else None
    
    # Initialize database store
    db = Database(settings.db_data)
    db_store = FixNestedTaskStore(db)
    
    try:
        result = process_fix_nested(
            filename,
            auth_payload,
            task_id=task_id,
            username=username,
            db_store=db_store
        )

        if result["success"]:
            flash(result["message"], "success")
            if result.get("details", {}).get("task_id"):
                flash(f"Task ID: {task_id}", "info")
        else:
            if result.get("details", {}).get("error"):
                flash(result["details"]["error"], "danger")

            flash(result["message"], "danger")
    finally:
        db.close()

    return redirect(url_for("fix_nested.fix_nested"))
