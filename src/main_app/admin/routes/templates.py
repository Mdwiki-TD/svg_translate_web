""" """

from __future__ import annotations

import json
import logging
from typing import Any, List, Tuple

from flask import (
    Blueprint,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue

from ...db.models import TemplateRecord
from ...db.services import (
    add_template_data,
    delete_template,
    get_template,
    get_template_by_title,
    list_templates,
    update_template_data,
)
from ..decorators import admin_required

logger = logging.getLogger(__name__)


def create_json_file() -> Tuple[Any, int]:
    """Create a JSON file containing all templates data.

    Returns:
        Tuple of (response, status_code) where response is either a Flask
        response object for file download (status 200) or an error message
        string with appropriate status code (404 for no templates, 500 for errors).
    """
    try:
        templates: List[TemplateRecord] = list_templates()

        if not templates:
            return "No templates found to export.", 404

        # Convert templates to a list of dictionaries
        templates_data = [
            {
                "title": template.title,
                "main_file": template.main_file,
                "last_world_file": template.last_world_file,
                "last_world_year": template.last_world_year,
                "source": template.source,
            }
            for template in templates
        ]

        # Create JSON content
        json_content = json.dumps(templates_data, indent=2, ensure_ascii=False)

        # Create response with JSON file
        response = make_response(json_content)
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Disposition"] = "attachment; filename=templates.json"

        return response, 200

    except LookupError as exc:
        logger.exception("Templates not found.")
        return f"Templates not found: {exc}", 404
    except Exception as exc:
        logger.exception("Failed to create JSON file.")
        return f"Failed to create JSON file: {exc}", 500


def _add_template() -> ResponseReturnValue:
    """Create a new template from the submitted title."""

    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required to add a template.", "danger")
        return redirect(url_for("admin.templates.dashboard"))

    main_file = request.form.get("main_file", "").strip()
    last_world_file = request.form.get("last_world_file", "").strip()
    source = request.form.get("source", "").strip()

    data = {
        "title": title,
        "main_file": main_file,
        "last_world_file": last_world_file,
        "source": source,
    }
    try:
        record = add_template_data(data)
    except ValueError:
        logger.exception("Unable to add template.")
        flash(f"Template '{title}' already exists", "warning")
    except LookupError:
        logger.exception("Unable to add template.")
        flash("Unable to add template.", "danger")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to add template.")
        flash("Unable to add template. Please try again.", "danger")
    else:
        flash(f"Template '{record.title}' added.", "success")

    return redirect(url_for("admin.templates.dashboard"))


def _update_template() -> ResponseReturnValue:
    """Update main_file for a template."""
    template_id = request.form.get("id", default=0, type=int)
    from_popup = request.form.get("from_popup") == "1"

    if not template_id:
        flash("Template ID is required to update a template.", "danger")
        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("admin.templates.dashboard"))

    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required to update a template.", "danger")
        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("admin.templates.dashboard"))

    main_file = request.form.get("main_file", "").strip()
    last_world_file = request.form.get("last_world_file", "").strip()
    source = request.form.get("source", "").strip()

    data = {
        "title": title,
        "main_file": main_file,
        "last_world_file": last_world_file,
        "source": source,
    }
    try:
        record = update_template_data(template_id, data)
    except LookupError:
        logger.exception("Unable to Update template.")
        flash(f"template with id {template_id} was not found", "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to update template.")
        flash("Unable to update template main file. Please try again.", "danger")
    else:
        flash(f"Template '{record.title}' main file: {main_file} updated.", "success")

    if from_popup:
        return render_template("admins/popup_action.html")
    return redirect(url_for("admin.templates.dashboard"))


def _delete_template(template_id: int) -> ResponseReturnValue:
    """Remove a template entirely."""
    from_popup = request.form.get("from_popup") == "1"

    try:
        template = get_template(template_id)
        title = template.title
        delete_template(template_id)
    except LookupError:
        logger.exception("Unable to delete template.")
        flash(f"template with id {template_id} was not found", "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to delete template.")
        flash("Unable to delete template. Please try again.", "danger")
    else:
        flash(f"Template '{title}' removed.", "success")

    if from_popup:
        return render_template("admins/popup_action.html")
    return redirect(url_for("admin.templates.dashboard"))


def _edit_template(template_id: int) -> ResponseReturnValue:
    """Render the edit template popup page."""
    try:
        template = get_template(template_id)
    except LookupError:
        return render_template(
            "admins/template_edit.html",
            error="Template not found",
            template=None,
        )

    return render_template(
        "admins/template_edit.html",
        template=template,
        error=None,
    )


def _edit_template_by_title(template_title: str) -> ResponseReturnValue:
    """Render the edit template popup page."""
    try:
        template = get_template_by_title(template_title)
    except LookupError:
        return render_template(
            "admins/template_edit.html",
            error="Template not found",
            template=None,
        )

    return render_template(
        "admins/template_edit.html",
        template=template,
        error=None,
    )


class Templates:
    def __init__(self) -> None:
        self.bp = Blueprint("templates", __name__, url_prefix="/templates")
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.route("/", methods=["GET"])
        @admin_required
        def dashboard():
            return render_template(
                "admins/templates.html",
            )

        @self.bp.get("/templates-need-update")
        @admin_required
        def templates_need_update() -> ResponseReturnValue:
            """Show templates that need year update based on OWID charts."""
            return render_template(
                "admins/templates_need_update.html",
            )

        @self.bp.post("/add")
        @admin_required
        def add_template() -> ResponseReturnValue:
            return _add_template()

        @self.bp.post("/update")
        @admin_required
        def update_template() -> ResponseReturnValue:
            return _update_template()

        @self.bp.post("/<int:template_id>/delete")
        @admin_required
        def delete_template(template_id: int) -> ResponseReturnValue:
            return _delete_template(template_id)

        @self.bp.get("/<int:template_id>/edit")
        @admin_required
        def edit_template(template_id: int) -> ResponseReturnValue:
            return _edit_template(template_id)

        @self.bp.get("/<path:template_title>/edit_by_title")
        @admin_required
        def edit_by_title(template_title: str) -> ResponseReturnValue:
            return _edit_template_by_title(template_title)

        @self.bp.get("/download-json")
        @admin_required
        def download_templates_json() -> ResponseReturnValue:
            """Download all templates as a json file."""

            response, status_code = create_json_file()

            # If the response is an error message (not a file), flash it and redirect
            if status_code != 200:
                flash(response, "warning" if status_code == 404 else "danger")
                return redirect(url_for("admin.templates.dashboard"))

            return response


templates_module = Templates()

__all__ = [
    "templates_module",
]
