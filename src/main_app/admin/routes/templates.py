"""Admin templates management routes rendered as MethodView classes."""

from __future__ import annotations

import json
import logging
from typing import Any

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
from flask.views import MethodView
from werkzeug.datastructures import ImmutableMultiDict

from ...database.exceptions import DuplicateRecordError
from ...database.models import TemplateRecord
from ...database.services import (
    TemplateService,
)
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class TemplatesRoutesFuncs:
    """Shared helpers used by the admin templates MethodViews."""

    def __init__(self) -> None:
        self.service = TemplateService()

    def _add_template(self, request_form: dict[str, Any] | ImmutableMultiDict) -> ResponseReturnValue:
        """Create a new template from the submitted title."""
        if isinstance(request_form, dict):
            request_form = ImmutableMultiDict(request_form)

        title = request_form.get("title", "").strip()
        if not title:
            flash("Title is required to add a template.", "danger")
            return redirect(url_for("adminpanel.templates.dashboard"))

        main_file = request_form.get("main_file", "").strip()
        last_world_file = request_form.get("last_world_file", "").strip()
        source = request_form.get("source", "").strip()

        data = {
            "title": title,
            "main_file": main_file,
            "last_world_file": last_world_file,
            "source": source,
        }
        try:
            self.service.add_template_data(data)
        except DuplicateRecordError:
            logger.exception("Unable to add template.")
            flash(f"Template '{title}' already exists", "warning")
        except LookupError:
            logger.exception("Unable to add template.")
            flash("Unable to add template.", "danger")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to add template.")
            flash("Unable to add template. Please try again.", "danger")
        else:
            flash(f"Template '{title}' added.", "success")

        return redirect(url_for("adminpanel.templates.dashboard"))

    def _update_template(self, request_form: dict[str, Any] | ImmutableMultiDict) -> ResponseReturnValue:
        """Update main_file for a template."""
        if isinstance(request_form, dict):
            request_form = ImmutableMultiDict(request_form)

        template_id = request_form.get("id", default=0, type=int)
        from_popup = request_form.get("from_popup") == "1"

        if not template_id:
            flash("Template ID is required to update a template.", "danger")
            if from_popup:
                return render_template("admins/popup_action.html")
            return redirect(url_for("adminpanel.templates.dashboard"))

        title = request_form.get("title", "").strip()
        if not title:
            flash("Title is required to update a template.", "danger")
            if from_popup:
                return render_template("admins/popup_action.html")
            return redirect(url_for("adminpanel.templates.dashboard"))

        main_file = request_form.get("main_file") or None
        last_world_file = request_form.get("last_world_file") or None
        last_world_year = request_form.get("last_world_year") or None
        source = request_form.get("source") or None

        data = {
            "title": title,
            "main_file": main_file,
            "last_world_file": last_world_file,
            "last_world_year": last_world_year,
            "source": source,
        }
        try:
            self.service.update_template_data(template_id, data)
        except LookupError:
            logger.exception("Unable to Update template.")
            flash(f"template with id {template_id} was not found", "warning")
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to update template.")
            flash("Unable to update template main file. Please try again.", "danger")
        else:
            flash(f"Template '{title}' main file: {main_file} updated.", "success")

        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("adminpanel.templates.dashboard"))

    def _delete_template(self, template_id: int, from_popup: bool = False) -> ResponseReturnValue:
        """Remove a template entirely."""
        template = self.service.get_template(template_id)

        if template:
            title = template.title
            deleted = self.service.delete(template_id)
            if deleted:
                flash(f"Template '{title}' removed.", "success")
            else:
                logger.error("Unable to delete template %s.", template_id)
                flash("Unable to delete template. Please try again.", "danger")
        else:
            flash(f"Template with id {template_id} was not found", "warning")

        if from_popup:
            return render_template("admins/popup_action.html")
        return redirect(url_for("adminpanel.templates.dashboard"))

    def edit_template(self, template_id: int) -> ResponseReturnValue:
        """Render the edit template popup page by id."""
        template = self.service.get_template(template_id)
        if not template:
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

    def edit_by_title(self, template_title: str) -> ResponseReturnValue:
        """Render the edit template popup page by title."""
        template = self.service.get_template_by_title(template_title)
        if not template:
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

    def download_templates_json(self) -> ResponseReturnValue:
        """Download all templates as a json file."""
        response, status_code = create_json_file()

        # If the response is an error message (not a file), flash it and redirect
        if status_code != 200:
            flash(response, "warning" if status_code == 404 else "danger")
            return redirect(url_for("adminpanel.templates.dashboard"))

        return response

    def create_json_file(self) -> tuple[Any, int]:
        """Create a JSON file containing all templates data.

        Returns:
            Tuple of (response, status_code) where response is either a Flask
            response object for file download (status 200) or an error message
            string with appropriate status code (404 for no templates, 500 for errors).
        """
        templates: list[TemplateRecord] = self.service.list()

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

        try:
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


class TemplatesDashboardView(TemplatesRoutesFuncs, MethodView):
    """View to render the admin templates dashboard."""

    decorators = [admin_required]

    def get(self) -> str:
        """Render the admin templates dashboard page."""
        return render_template(
            "admins/templates.html",
        )


class TemplatesNeedUpdateView(TemplatesRoutesFuncs, MethodView):
    """View to render the templates that need a year update."""

    decorators = [admin_required]

    def get(self) -> str:
        """Show templates that need year update based on OWID charts."""
        return render_template(
            "admins/templates_need_update.html",
        )


class AddTemplateView(TemplatesRoutesFuncs, MethodView):
    """View to add a single template from the dashboard form."""

    decorators = [admin_required]

    def post(self) -> ResponseReturnValue:
        """Create a new template from the submitted form."""
        return self._add_template(request.form)


class UpdateTemplateView(TemplatesRoutesFuncs, MethodView):
    """View to apply a template update submitted from the edit form."""

    decorators = [admin_required]

    def post(self) -> ResponseReturnValue:
        """Update the template identified by the submitted form id."""
        return self._update_template(request.form)


class DeleteTemplateView(TemplatesRoutesFuncs, MethodView):
    """View to delete a single template."""

    decorators = [admin_required]

    def post(self, template_id: int) -> ResponseReturnValue:
        """Remove the template with the given id."""
        from_popup = request.form.get("from_popup") == "1"
        return self._delete_template(template_id, from_popup)


class EditTemplateView(TemplatesRoutesFuncs, MethodView):
    """View to render the edit template popup page by id."""

    decorators = [admin_required]

    def get(self, template_id: int) -> ResponseReturnValue:
        """Render the edit template popup page for the given id."""
        return self.edit_template(template_id)


class EditTemplateByTitleView(TemplatesRoutesFuncs, MethodView):
    """View to render the edit template popup page by title."""

    decorators = [admin_required]

    def get(self, template_title: str) -> ResponseReturnValue:
        """Render the edit template popup page for the given title."""
        return self.edit_by_title(template_title)


class DownloadTemplatesJsonView(TemplatesRoutesFuncs, MethodView):
    """View to download all templates as a JSON file."""

    decorators = [admin_required]

    def get(self) -> ResponseReturnValue:
        """Download all templates as a json file."""
        return self.download_templates_json()


class TemplatesRoutes(TemplatesRoutesFuncs):
    """Registrar class to bind admin templates MethodViews to a Blueprint."""

    def register(self, bp: Blueprint) -> None:
        """Register admin templates URL rules on the provided blueprint with admin protection."""
        bp.add_url_rule("/", view_func=TemplatesDashboardView.as_view("dashboard"))
        bp.add_url_rule("/add", view_func=AddTemplateView.as_view("add_template"))
        bp.add_url_rule("/update", view_func=UpdateTemplateView.as_view("update_template"))
        bp.add_url_rule(
            "/<int:template_id>/delete",
            view_func=DeleteTemplateView.as_view("delete_template"),
        )
        bp.add_url_rule(
            "/templates-need-update",
            view_func=TemplatesNeedUpdateView.as_view("templates_need_update"),
        )
        bp.add_url_rule(
            "/<int:template_id>/edit",
            view_func=EditTemplateView.as_view("edit_template"),
        )
        bp.add_url_rule(
            "/<path:template_title>/edit_by_title",
            view_func=EditTemplateByTitleView.as_view("edit_by_title"),
        )
        bp.add_url_rule(
            "/download-json",
            view_func=DownloadTemplatesJsonView.as_view("download_templates_json"),
        )


def create_json_file():
    """Module-level entry point kept for backward compatibility."""
    return TemplatesRoutesFuncs().create_json_file()


__all__ = [
    "TemplatesRoutes",
]
