"""Admin-only routes for managing application settings, built on MethodView."""

from __future__ import annotations

import logging
import re
from typing import Any

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from flask.views import MethodView
from werkzeug.datastructures import ImmutableMultiDict

from ...database.services import SettingsService
from ..decorators import admin_required

logger = logging.getLogger(__name__)


def _parse_setting_value(v_type: str, raw_val: str) -> tuple[Any, bool]:
    """Coerce a submitted form value, returning ``(value, success)``."""
    if v_type == "boolean":
        return raw_val == "on", True
    elif v_type == "integer":
        try:
            return int(raw_val), True
        except (TypeError, ValueError):
            return 0, False
    else:
        return raw_val, True


class SettingsFuncs:
    """Shared service access and form-processing logic for the settings views."""

    def __init__(self) -> None:
        self.service = SettingsService()

    def settings_update_form(self, request_form: ImmutableMultiDict) -> tuple[list[str], list[str]]:
        """Apply the submitted settings form, returning ``(failed_keys, deleted_keys)``."""
        all_settings = self.service.get_all_settings_raw()
        failed_keys: list[str] = []
        deleted_keys: list[str] = []

        for setting in all_settings:
            key = setting["key"]
            v_type = setting["value_type"]
            form_key = f"setting_{key}"
            delete_key = f"delete_{key}"

            # Check if marked for deletion
            if request_form.get(delete_key) == "on":
                if self.service.delete_setting_by_key(key):
                    deleted_keys.append(key)
                else:
                    failed_keys.append(key)
                continue

            if v_type == "boolean":
                raw_val = request_form.get(form_key, "")
            elif form_key in request_form:
                raw_val = request_form.get(form_key, "")
            else:
                continue

            value, success = _parse_setting_value(v_type, raw_val)
            if not success:
                failed_keys.append(key)
                continue

            if not self.service.update_setting(key, value, v_type):
                failed_keys.append(key)

        return failed_keys, deleted_keys


class SettingsDashboardView(SettingsFuncs, MethodView):
    """View rendering the settings dashboard."""

    decorators = [admin_required]

    def get(self) -> str:
        """List every stored setting as a raw table."""
        settings_list = self.service.get_all_settings_raw()
        return render_template(
            "admins/settings.html",
            settings_list=settings_list,
        )


class SettingsCreateView(SettingsFuncs, MethodView):
    """View creating a single new setting from the submitted form."""

    decorators = [admin_required]

    def post(self) -> ResponseReturnValue:
        """Validate the key and store the setting, then redirect to the dashboard."""
        key = request.form.get("key", "").strip()
        title = request.form.get("title", "").strip()
        value_type = request.form.get("value_type", "boolean").strip()

        if not re.fullmatch(r"[a-z][a-z0-9_]{0,189}", key):
            flash(
                "Key must start with a lowercase letter and contain only lowercase letters, digits, and underscores.",
                "danger",
            )
            return redirect(url_for("adminpanel.settings.dashboard"))

        if key and title:
            success = self.service.create_setting(key, title, value_type)
            if success:
                flash("Setting created successfully.", "success")
            else:
                flash("Setting could not be created or already exists.", "danger")
        else:
            flash("Key and Title are required.", "danger")

        return redirect(url_for("adminpanel.settings.dashboard"))


class SettingsUpdateView(SettingsFuncs, MethodView):
    """View applying the bulk settings update form."""

    decorators = [admin_required]

    def post(self) -> ResponseReturnValue:
        """Apply every changed setting, then redirect to the dashboard."""
        failed_keys, deleted_keys = self.settings_update_form(request.form)
        # Invalidate runtime cache only if all updates succeeded
        if not failed_keys:
            if deleted_keys:
                flash(f"Deleted settings: {', '.join(deleted_keys)}. ", "success")

            flash("Settings updated successfully.", "success")
        else:
            flash(f"Some settings failed to update: {', '.join(failed_keys)}", "danger")
        return redirect(url_for("adminpanel.settings.dashboard"))


class SettingsRoutes:
    """Settings routes registrar using class-based views."""

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register the dashboard, create and update endpoints."""
        bp.add_url_rule(
            "/",
            view_func=SettingsDashboardView.as_view("dashboard"),
            methods=["GET"],
        )
        bp.add_url_rule(
            "/create",
            view_func=SettingsCreateView.as_view("create"),
            methods=["POST"],
        )
        bp.add_url_rule(
            "/update",
            view_func=SettingsUpdateView.as_view("update"),
            methods=["POST"],
        )


__all__ = [
    "SettingsRoutes",
]
