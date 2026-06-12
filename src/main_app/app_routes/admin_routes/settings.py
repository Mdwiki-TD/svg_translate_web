"""Admin-only routes for managing application settings."""

from __future__ import annotations

import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ...db.services import (
    create_setting,
    get_all_settings_raw,
    settings_update_form,
)
from ..admin.admins_required import admin_required


class SettingsRoutes:
    def __init__(self) -> None:
        self.bp = Blueprint("settings", __name__, url_prefix="/settings")
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.get("/")
        @admin_required
        def dashboard():
            all_settings = get_all_settings_raw()
            return render_template("admins/settings.html", settings_list=all_settings)

        @self.bp.post("/create")
        @admin_required
        def settings_create():
            key = request.form.get("key", "").strip()
            title = request.form.get("title", "").strip()
            value_type = request.form.get("value_type", "boolean").strip()

            if not re.fullmatch(r"[a-z][a-z0-9_]{0,189}", key):
                flash(
                    "Key must start with a lowercase letter and contain only lowercase letters, digits, and underscores.",
                    "danger",
                )
                return redirect(url_for("admin.settings.dashboard"))
            if key and title:
                success = create_setting(key, title, value_type)
                if success:
                    flash("Setting created successfully.", "success")
                else:
                    flash("Setting could not be created or already exists.", "danger")
            else:
                flash("Key and Title are required.", "danger")

            return redirect(url_for("admin.settings.dashboard"))

        @self.bp.post("/update")
        @admin_required
        def settings_update():
            failed_keys, deleted_keys = settings_update_form(request.form)
            # Invalidate runtime cache only if all updates succeeded
            if not failed_keys:
                if deleted_keys:
                    flash(f"Deleted settings: {', '.join(deleted_keys)}. ", "success")

                flash("Settings updated successfully.", "success")
            else:
                flash(f"Some settings failed to update: {', '.join(failed_keys)}", "danger")
            return redirect(url_for("admin.settings.dashboard"))


settings_module = SettingsRoutes()

__all__ = [
    "settings_module",
]
