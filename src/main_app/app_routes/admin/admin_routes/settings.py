"""Admin-only routes for managing application settings."""

from __future__ import annotations
import json

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ....admins.admins_required import admin_required
from ....config import settings


class SettingsRoutes:
    def __init__(self, bp_admin: Blueprint):
        from ....db.db_Settings import SettingsDB

        @bp_admin.get("/settings")
        @admin_required
        def settings_view():
            db_settings = SettingsDB(settings.database_data)
            all_settings = db_settings.get_raw_all()
            return render_template("admins/settings.html", settings_list=all_settings)

        @bp_admin.post("/settings/create")
        @admin_required
        def settings_create():
            db_settings = SettingsDB(settings.database_data)
            key = request.form.get("key", "").strip()
            title = request.form.get("title", "").strip()
            value_type = request.form.get("value_type", "boolean").strip()

            if value_type == "boolean":
                value = False
            elif value_type == "integer":
                value = 0
            elif value_type == "json":
                value = {}
            else:
                value = ""

            if key and title:
                success = db_settings.create_setting(key, title, value_type, value)
                if success:
                    flash("Setting created successfully.", "success")
                else:
                    flash("Setting could not be created or already exists.", "danger")
            else:
                flash("Key and Title are required.", "danger")

            return redirect(url_for("admin.settings_view"))

        @bp_admin.post("/settings/update")
        @admin_required
        def settings_update():
            db_settings = SettingsDB(settings.database_data)
            all_settings = db_settings.get_raw_all()
            failed_keys: list[str] = []

            for s in all_settings:
                key = s["key"]
                v_type = s["value_type"]
                form_key = f"setting_{key}"

                if v_type == "boolean":
                    value = request.form.get(form_key) == "on"
                    if not db_settings.update_setting(key, value, v_type):
                        failed_keys.append(key)
                else:
                    # check if it is included in the dictionary (distinguish unchecked checkboxes vs missing files)
                    if form_key in request.form:
                        raw_val = request.form.get(form_key, "")
                        if v_type == "integer":
                            try:
                                value = int(raw_val)
                            except ValueError:
                                value = 0
                        elif v_type == "json":
                            try:
                                value = json.loads(raw_val)
                            except Exception:
                                failed_keys.append(key)
                                continue
                        else:
                            value = raw_val
                        if not db_settings.update_setting(key, value, v_type):
                            failed_keys.append(key)

            # Invalidate runtime cache only if all updates succeeded
            if not failed_keys:
                settings.dynamic.invalidate()
                flash("Settings updated successfully.", "success")
            else:
                flash(f"Some settings failed to update: {', '.join(failed_keys)}", "danger")
            return redirect(url_for("admin.settings_view"))
