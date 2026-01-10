import base64
import json
import logging
import shutil
import tempfile
import uuid
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast

from CopySVGTranslation import extract
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ...admins.admin_service import active_coordinators
from ...config import settings
from ...db.db_class import Database
from ...db.fix_nested_task_store import FixNestedTaskStore
from ...routes_utils import load_auth_payload
from ...tasks.downloads.download import download_one_file
from ...users.current import current_user
from .fix_utils import process_fix_nested, process_fix_nested_file_simple

bp_fix_nested = Blueprint("fix_nested", __name__, url_prefix="/fix_nested")
logger = logging.getLogger("svg_translate")

# Session key for preserving filename across OAuth redirect
FIX_NESTED_FILENAME_KEY = "fix_nested_filename"

F = TypeVar("F", bound=Callable[..., Any])


def _get_commons_file_url(filename: str) -> str:
    """Generate Wikimedia Commons URL for a file."""
    # URL encode the filename for the URL
    from urllib.parse import quote

    encoded_name = quote(filename.replace(" ", "_"))
    return f"https://commons.wikimedia.org/wiki/File:{encoded_name}"


def oauth_required_with_filename_preservation(func: F) -> F:
    """Custom OAuth decorator that preserves filename in session before redirect."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        if settings.use_mw_oauth and not current_user() and not settings.is_localhost(request.host):
            # Save filename to session before redirecting to OAuth
            filename = request.form.get("filename", "").strip()
            if filename:
                session[FIX_NESTED_FILENAME_KEY] = filename
            session["post_login_redirect"] = request.url
            return redirect(url_for("auth.login"))
        return func(*args, **kwargs)

    return cast(F, wrapper)


@bp_fix_nested.route("/", methods=["GET"])
# @oauth_required
def fix_nested():
    # Restore filename from session if available (e.g., after OAuth redirect)
    filename = session.pop(FIX_NESTED_FILENAME_KEY, "")
    return render_template("fix_nested/form.html", filename=filename)


@bp_fix_nested.route("/", methods=["POST"])
@oauth_required_with_filename_preservation
def fix_nested_post():
    # POST logic
    filename = request.form.get("filename", "").strip()

    # Remove "File:" prefix if present (keep original for display)
    original_filename = filename
    if filename.lower().startswith("file:"):
        filename = filename[5:].lstrip()

    if not filename:
        flash("Please provide a file name", "danger")
        return render_template("fix_nested/form.html", filename=original_filename)

    # Generate unique task ID
    task_id = str(uuid.uuid4())
    logger.info(f"Starting fix_nested task {task_id} for file: {filename}")

    current_user_obj = current_user()

    if not current_user_obj:
        flash("You must be logged in to perform this action.", "danger")
        return render_template("fix_nested/form.html", filename=original_filename)

    auth_payload = load_auth_payload(current_user_obj)
    username = current_user_obj.username if current_user_obj else None

    # Initialize database store

    with Database(settings.db_data) as db:
        db_store = FixNestedTaskStore(db)
        result = process_fix_nested(filename, auth_payload, task_id=task_id, username=username, db_store=db_store)

    commons_link = None

    if result["success"]:
        flash(result["message"], "success")
        if result.get("details", {}).get("task_id"):
            flash(f"Task ID: {task_id}", "info")
        # Generate Commons link for successful upload
        commons_link = _get_commons_file_url(filename)
    else:
        if result.get("details", {}).get("error"):
            flash(result["details"]["error"], "danger")
        error_details = result.get("details", {}).get("error_details", "")
        # flash error_details if user is_admin from context_user
        if username in active_coordinators() and error_details:
            flash(error_details, "danger")

        flash(result["message"], "danger")
        return render_template("fix_nested/form.html", filename=original_filename)

    # Preserve filename in input field regardless of result
    return render_template("fix_nested/form.html", filename=original_filename, commons_link=commons_link)


@bp_fix_nested.route("/upload", methods=["POST", "GET"])
@oauth_required_with_filename_preservation
def fix_nested_by_upload_file():
    if request.method == "GET":
        return render_template("fix_nested/upload_form.html")

    # POST logic
    file = request.files.get("file")
    if not file or not file.filename.endswith(".svg"):
        flash("Please upload a valid SVG file", "danger")
        return render_template("fix_nested/upload_form.html")

    original_filename = file.filename

    if not original_filename:
        flash("Please provide a valid file", "danger")
        return render_template("fix_nested/upload_form.html")

    current_user_obj = current_user()

    if not current_user_obj and not settings.is_localhost(request.host):
        flash("You must be logged in to perform this action.", "danger")
        return render_template("fix_nested/upload_form.html")

    result = process_fix_nested_file_simple(file)

    if result["success"]:
        flash(result["message"], "success")
    else:
        if result.get("details", {}).get("error"):
            flash(result["details"]["error"], "danger")

        flash(result["message"], "danger")
        return render_template("fix_nested/upload_form.html")

    result_file_path = result.get("file_path")
    if not result_file_path:
        flash("Failed to process SVG file", "danger")
        return render_template(
            "fix_nested/upload_form.html",
        )

    # flash("File processed successfully. Download below.", "success")
    # encode filecontent to base64 for download link
    b64_content = ""
    try:
        with open(result_file_path, "rb") as f:
            file_content = f.read()
        b64_content = base64.b64encode(file_content).decode("utf-8")
    finally:
        shutil.rmtree(result_file_path.parent)

    download_link = f"data:image/svg+xml;base64,{b64_content}"
    return render_template(
        "fix_nested/upload_form.html", filename=f"fixed_{original_filename}", download_link=download_link
    )


# Session key for preserving filename across OAuth redirect for extract
EXTRACT_FILENAME_KEY = "extract_filename"


@bp_fix_nested.route("/extract", methods=["GET"])
def extract_translations():
    """Display form to extract translations from an SVG file."""
    # Restore filename from session if available (e.g., after OAuth redirect)
    filename = session.pop(EXTRACT_FILENAME_KEY, "")
    return render_template("fix_nested/extract_form.html", filename=filename)


@bp_fix_nested.route("/extract", methods=["POST"])
def extract_translations_post():
    """Process SVG file and extract translations."""
    filename = request.form.get("filename", "").strip()

    # Remove "File:" prefix if present (keep original for display)
    original_filename = filename
    if filename.lower().startswith("file:"):
        filename = filename[5:].lstrip()

    if not filename:
        flash("Please provide a file name", "danger")
        return render_template("fix_nested/extract_form.html", filename=original_filename)

    logger.info(f"Starting extract translations for file: {filename}")

    # Create temporary directory for download
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Download the file
        result = download_one_file(title=filename, out_dir=temp_dir, i=0, overwrite=True)

        if result.get("result") != "success" or not result.get("path"):
            flash(f"Failed to download file: {filename}", "danger")
            return render_template("fix_nested/extract_form.html", filename=original_filename)

        file_path = Path(result["path"])

        # Extract translations using CopySVGTranslation
        try:
            translations = extract(svg_file_path=file_path, case_insensitive=True)
        except Exception as e:
            logger.error(f"Error extracting translations: {e}", exc_info=True)
            flash(f"Error extracting translations: {str(e)}", "danger")
            return render_template("fix_nested/extract_form.html", filename=original_filename)

        # Convert translations to pretty JSON for display
        translations_json = json.dumps(translations, ensure_ascii=False, indent=4)

        flash("Translations extracted successfully", "success")
        return render_template(
            "fix_nested/extract_form.html",
            filename=original_filename,
            translations_json=translations_json,
            translations=translations,
        )

    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
