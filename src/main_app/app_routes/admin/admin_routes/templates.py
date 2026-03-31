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

from ..admins_required import admin_required
from ....db import TemplateRecord
from ....services import template_service
from ....services.users_service import current_user

logger = logging.getLogger(__name__)


def create_json_file() -> Tuple[Any, int]:
    """Create a JSON file containing all templates data.

    Returns:
        Tuple of (response, status_code) where response is either a Flask
        response object for file download (status 200) or an error message
        string with appropriate status code (404 for no templates, 500 for errors).
    """
    try:
        templates: List[TemplateRecord] = template_service.list_templates()

        if not templates:
            return "No templates found to export.", 404

        # Convert templates to a list of dictionaries
        templates_data = [
            {
                "title": template.title,
                "main_file": template.main_file,
                "last_world_file": template.last_world_file,
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


def _templates_dashboard():
    """Render the template management dashboard."""

    user = current_user()
    templates: List[TemplateRecord] = template_service.list_templates()
    total = len(templates)
    summary = {
        "total": len(templates),
        "with_main_file": len([template for template in templates if template.main_file]),
        "with_last_world_file": len([t for t in templates if t.last_world_file]),
        "with_source": len([template for template in templates if template.source]),
    }
    return render_template(
        "admins/templates.html",
        current_user=user,
        templates=templates,
        total_templates=total,
        summary=summary,
    )


def _add_template() -> ResponseReturnValue:
    """Create a new template from the submitted title."""

    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required to add a template.", "danger")
        return redirect(url_for("admin.templates_dashboard"))

    main_file = request.form.get("main_file", "").strip()
    last_world_file = request.form.get("last_world_file", "").strip()
    source = request.form.get("source", "").strip()

    try:
        record = template_service.add_template(title, main_file, last_world_file, source)
    except ValueError as exc:
        logger.exception("Unable to add template.")
        flash(str(exc), "warning")
    except LookupError as exc:
        logger.exception("Unable to add template.")
        flash(str(exc), "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to add template.")
        flash("Unable to add template. Please try again.", "danger")
    else:
        flash(f"Template '{record.title}' added.", "success")

    return redirect(url_for("admin.templates_dashboard"))


def _update_template() -> ResponseReturnValue:
    """Update main_file for a template."""
    template_id = request.form.get("id", default=0, type=int)
    from_popup = request.form.get("from_popup") == "1"

    if not template_id:
        flash("Template ID is required to update a template.", "danger")
        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("admin.templates_dashboard"))

    title = request.form.get("title", "").strip()
    if not title:
        flash("Title is required to update a template.", "danger")
        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("admin.templates_dashboard"))

    main_file = request.form.get("main_file", "").strip()
    last_world_file = request.form.get("last_world_file", "").strip()
    source = request.form.get("source", "").strip()

    try:
        record = template_service.update_template(template_id, title, main_file, last_world_file, source)
    except LookupError as exc:
        logger.exception("Unable to Update template.")
        flash(str(exc), "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to update template.")
        flash("Unable to update template main file. Please try again.", "danger")
    else:
        flash(f"Template '{record.title}' main file: {main_file} updated.", "success")

    if from_popup:
        return render_template("admins/popup_action.html")
    return redirect(url_for("admin.templates_dashboard"))


def _delete_template(template_id: int) -> ResponseReturnValue:
    """Remove a template entirely."""
    from_popup = request.form.get("from_popup") == "1"

    try:
        record = template_service.delete_template(template_id)
    except LookupError as exc:
        logger.exception("Unable to delete template.")
        flash(str(exc), "warning")
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to delete template.")
        flash("Unable to delete template. Please try again.", "danger")
    else:
        flash(f"Template '{record.title}' removed.", "success")

    if from_popup:
        return render_template("admins/popup_action.html")
    return redirect(url_for("admin.templates_dashboard"))


def _edit_template(template_id: int) -> ResponseReturnValue:
    """Render the edit template popup page."""
    try:
        template = template_service.get_template(template_id)
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
    def __init__(self, bp_admin: Blueprint):
        @bp_admin.get("/templates")
        @admin_required
        def templates_dashboard():
            return _templates_dashboard()

        @bp_admin.post("/templates/add")
        @admin_required
        def add_template() -> ResponseReturnValue:
            return _add_template()

        @bp_admin.post("/templates/update")
        @admin_required
        def update_template() -> ResponseReturnValue:
            return _update_template()

        @bp_admin.post("/templates/<int:template_id>/delete")
        @admin_required
        def delete_template(template_id: int) -> ResponseReturnValue:
            return _delete_template(template_id)

        @bp_admin.get("/templates/<int:template_id>/edit")
        @admin_required
        def edit_template(template_id: int) -> ResponseReturnValue:
            return _edit_template(template_id)

        @bp_admin.get("/templates/download-json")
        @admin_required
        def download_templates_json() -> ResponseReturnValue:
            """Download all templates as a json file."""

            response, status_code = create_json_file()

            # If the response is an error message (not a file), flash it and redirect
            if status_code != 200:
                flash(response, "warning" if status_code == 404 else "danger")
                return redirect(url_for("admin.templates_dashboard"))

            return response
