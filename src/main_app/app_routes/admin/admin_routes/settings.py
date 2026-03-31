"""Admin-only routes for managing application settings."""

from __future__ import annotations

import json
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..admins_required import admin_required
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

            if not re.fullmatch(r"[a-z][a-z0-9_]{0,189}", key):
                flash(
                    "Key must start with a lowercase letter and contain only lowercase letters, digits, and underscores.",
                    "danger",
                )
                return redirect(url_for("admin.settings_view"))

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

        def _parse_setting_value(v_type: str, raw_val: str) -> tuple[any, bool]:
            """Returns (value, success)"""
            if v_type == "boolean":
                return raw_val == "on", True
            elif v_type == "integer":
                try:
                    return int(raw_val), True
                except ValueError:
                    return 0, True
            elif v_type == "json":
                try:
                    return json.loads(raw_val), True
                except Exception:
                    return None, False
            else:
                return raw_val, True

        @bp_admin.post("/settings/update")
        @admin_required
        def settings_update():
            db_settings = SettingsDB(settings.database_data)
            all_settings = db_settings.get_raw_all()
            failed_keys: list[str] = []
            deleted_keys: list[str] = []

            for s in all_settings:
                key = s["key"]
                v_type = s["value_type"]
                form_key = f"setting_{key}"
                delete_key = f"delete_{key}"

                # Check if marked for deletion
                if request.form.get(delete_key) == "on":
                    if db_settings.delete_setting(key):
                        deleted_keys.append(key)
                    else:
                        failed_keys.append(key)
                    continue

                if v_type == "boolean":
                    raw_val = request.form.get(form_key, "")
                elif form_key in request.form:
                    raw_val = request.form.get(form_key, "")
                else:
                    continue

                value, success = _parse_setting_value(v_type, raw_val)
                if not success or not db_settings.update_setting(key, value, v_type):
                    failed_keys.append(key)

            # Invalidate runtime cache only if all updates succeeded
            if not failed_keys:
                settings.dynamic.invalidate()
                if deleted_keys:
                    flash(f"Deleted settings: {', '.join(deleted_keys)}. ", "success")

                flash("Settings updated successfully.", "success")
            else:
                flash(f"Some settings failed to update: {', '.join(failed_keys)}", "danger")
            return redirect(url_for("admin.settings_view"))
