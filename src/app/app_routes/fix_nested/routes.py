
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for

from ...routes_utils import load_auth_payload
from .fix_utils import process_fix_nested
from ...users.current import current_user, oauth_required

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
        filename = filename.split(":", 1)[1].strip()

    if not filename:
        flash("Please provide a file name", "danger")
        return redirect(url_for("fix_nested.fix_nested"))

    # Import processing function

    current_user_obj = current_user()
    auth_payload = load_auth_payload(current_user_obj)
    result = process_fix_nested(filename, auth_payload)

    if result["success"]:
        flash(result["message"], "success")
    else:
        if result.get("details", {}).get("error"):
            flash(result["details"]["error"], "danger")

        flash(result["message"], "danger")

    return redirect(url_for("fix_nested.fix_nested"))
