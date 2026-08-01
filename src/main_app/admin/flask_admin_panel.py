"""Admin blueprint package."""

from flask import Flask, abort, redirect, request, url_for
from flask_admin import Admin, AdminIndexView  # , BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_babel import Babel

from ..public.auth.utils import load_user

from dataclasses import dataclass, field
from typing import Any


from ..db.models import (  # UserTokenRecord,; TemplateNeedUpdateView,
    AdminUserRecord,
    JobRecord,
    OwidChartRecord,
    OwidSlugRedirectRecord,
    SettingRecord,
    TemplateRecord,
    UserRecord,
)


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self) -> bool:
        user = load_user()
        return bool(user and user.is_active_admin)

    def inaccessible_callback(self, name: str, **kwargs: Any) -> Any:
        user = load_user()
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
        user = load_user()
        return bool(user and user.is_active_admin)

    def inaccessible_callback(self, name: str, **kwargs: Any) -> Any:
        user = load_user()
        if not user:
            return redirect(url_for("auth.login", next=request.url))
        abort(403)


# 1. Dataclass to represent individual models with optional parameters like custom names
@dataclass
class ModelItem:
    model: Any
    name: str | None = None


# 2. Dataclass to represent an Admin Category
@dataclass
class AdminCategory:
    name: str | None  # None for uncategorized/standalone models
    icon_value: str = "fa-folder"
    models: list[Any] = field(default_factory=list)  # Accepts a raw model or a ModelItem instance
    icon_type: str = "fa"
    class_name: Any = None


# 3. Primary categories configuration
categories: list[AdminCategory] = [
    AdminCategory(
        name="Templates",
        icon_value="fa-cubes",
        models=[
            TemplateRecord,
            # ModelItem(model=TemplateNeedUpdateView, name="Templates Need Update"),
        ],
    ),
    AdminCategory(
        name="OwidCharts",
        icon_value="fa-chart-line",  # Changed icon to better represent charts/analytics
        models=[
            ModelItem(model=OwidChartRecord, name="OwidChartRecord"),
            ModelItem(model=OwidSlugRedirectRecord, name="OwidSlugRedirectRecord"),
        ],
    ),
    AdminCategory(
        name="Users",
        icon_value="fa-users",
        models=[
            AdminUserRecord,
            UserRecord,
        ],
    ),
    # Standalone category for models without a specific category group
    AdminCategory(
        name=None,
        models=[
            JobRecord,
            SettingRecord,
        ],
    ),
]


def add_admin_dashboard(app: Flask, _db) -> None:
    babel = Babel(app)  # pyright: ignore
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

    add_views_new(_db, admin)
    # add_views(_db, admin)

def add_views_new(_db, admin):
    # 4. Dynamically build and construct WrapModelView instances
    all_models = []

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

def add_views(_db, admin):
    admin.add_category(
        name="Templates",
        class_name=None,
        icon_type="fa",
        icon_value="fa-cubes",
    )

    admin.add_category(
        name="OwidCharts",
        class_name=None,
        icon_type="fa",
        icon_value="fa-cubes",
    )

    admin.add_category(
        name="Users",
        class_name=None,
        icon_type="fa",
        icon_value="fa-users",
    )

    all_models = [
        WrapModelView(TemplateRecord, _db, category="Templates"),
        # WrapModelView(TemplateNeedUpdateView, _db, name="Templates Need Update", category="Templates"),
        WrapModelView(OwidChartRecord, _db, name="OwidChartRecord", category="OwidCharts"),
        WrapModelView(OwidSlugRedirectRecord, _db, name="OwidSlugRedirectRecord", category="OwidCharts"),
        WrapModelView(AdminUserRecord, _db, category="Users"),
        WrapModelView(UserRecord, _db, category="Users"),
        WrapModelView(JobRecord, _db),
        WrapModelView(SettingRecord, _db),
    ]
    admin.add_views(*all_models)


__all__ = [
    "add_admin_dashboard",
]
