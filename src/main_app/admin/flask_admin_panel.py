"""Admin blueprint package."""

from typing import Any

from flask import Flask, abort, redirect, request, url_for
from flask_admin import Admin, AdminIndexView  # , BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_babel import Babel
from flask_sqlalchemy import SQLAlchemy

from ..public.auth.utils import get_current_user
from .flask_admin_panel_models import ModelItem, categories


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self) -> bool:
        user = get_current_user()
        return bool(user and user.is_active_admin)

    def inaccessible_callback(self, name: str, **kwargs: Any) -> Any:
        user = get_current_user()
        if not user:
            return redirect(url_for("auth.login", next=request.url))
        abort(403)


class WrapModelView(ModelView):
    ignore_hidden = True
    form_excluded_columns = ("created_at", "updated_at", "token")
    column_display_actions: bool = True
    action_disallowed_list = ["delete"]
    page_size: int = 50
    # edit_modal: bool = True
    # create_modal: bool = True
    can_edit: bool = True
    can_delete: bool = False
    can_view_details: bool = True

    def is_accessible(self) -> bool:
        user = get_current_user()
        return bool(user and user.is_active_admin)

    def inaccessible_callback(self, name: str, **kwargs: Any) -> Any:
        user = get_current_user()
        if not user:
            return redirect(url_for("auth.login", next=request.url))
        abort(403)


def add_admin_dashboard(app: Flask, _db: SQLAlchemy) -> None:
    babel = Babel(app)
    # Initialize Admin and add views
    theme = Bootstrap4Theme(
        base_template="admin/index_with_sidebar.html",
        swatch="default",
        fluid=True,
    )
    admin = Admin(
        app,
        name="DB admin",
        theme=theme,
        endpoint=None,
        index_view=MyAdminIndexView(
            name="DB admin",
            template="admin/index_with_sidebar.html",
            url="/adminpanel/db_admin",
        ),
    )

    add_views(_db, admin)


def add_views(_db, admin):
    # 4. Dynamically build and construct WrapModelView instances
    all_models = []

    # register all models
    for cat in categories:
        # Register category only if a category name is defined
        if cat.name:
            admin.add_category(
                name=cat.name,
                class_name=cat.class_name,
                icon_type=cat.icon_type,
                icon_value=cat.icon_value,
            )

        # Process and wrap models within the category
        for item in cat.models:
            if isinstance(item, ModelItem):
                kwargs = {"category": cat.name} if cat.name else {}
                if item.name:
                    kwargs["name"] = item.name
                all_models.append(WrapModelView(item.model, _db, **kwargs))
            else:
                kwargs = {"category": cat.name} if cat.name else {}
                all_models.append(WrapModelView(item, _db, **kwargs))

    # 5. Register all wrapped view instances in a single call
    admin.add_views(*all_models)


__all__ = [
    "add_admin_dashboard",
]
