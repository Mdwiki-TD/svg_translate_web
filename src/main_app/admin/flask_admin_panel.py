"""Admin blueprint package."""

from flask import Flask
from flask_admin import Admin, AdminIndexView  # , BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme
from flask_babel import Babel

from ..db.models import (  # UserTokenRecord,; TemplateNeedUpdateView,
    AdminUserRecord,
    JobRecord,
    OwidChartRecord,
    OwidSlugRedirectRecord,
    SettingRecord,
    TemplateRecord,
    UserRecord,
)


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
        index_view=AdminIndexView(
            name="DB admin", template="admin/index_with_sidebar.html", url="/adminpanel/db_admin"
        ),
    )

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
