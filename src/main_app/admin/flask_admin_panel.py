"""Admin blueprint package."""

from flask import Flask
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.theme import Bootstrap4Theme

from ..db.models import (
    AdminUserRecord,
    JobRecord,
    OwidChartRecord,
    OwidChartTemplateView,
    OwidSlugRedirectRecord,
    SettingRecord,
    TemplateNeedUpdateView,
    TemplateRecord,
    UserRecord,
)


class WrapModelView(ModelView):
    form_excluded_columns = ('created_at', 'token')
    column_display_actions: bool = True
    action_disallowed_list = ['delete']
    page_size: int = 50
    edit_modal: bool = True
    create_modal: bool = True
    can_view_details: bool = True

def add_admin_dashboard(app: Flask, _db) -> None:
    # Initialize Admin and add views
    theme = Bootstrap4Theme(
        base_template="admin/index.html",
        swatch="cerulean",
        fluid=True,
    )
    admin = Admin(
        app,
        name="microblog",
        theme=theme,
        endpoint=None,
    )

    admin.add_category(
        name="Main",
        class_name=None,
        icon_type=None,
        icon_value=None,
    )

    main_models = [
        WrapModelView(TemplateRecord, _db, category="Main"),
        WrapModelView(TemplateNeedUpdateView, _db, name="Templates Need Update", category="Main"),
        WrapModelView(OwidChartRecord, _db, category="Main", name="OWID Charts"),
        WrapModelView(OwidSlugRedirectRecord, _db, category="Main"),
    ]
    admin.add_views(*main_models)

    admin.add_category(
        name="Users",
        class_name=None,
        icon_type=None,
        icon_value=None,
    )

    users_models = [
        WrapModelView(AdminUserRecord, _db, category="Users"),
        WrapModelView(UserRecord, _db, category="Users"),
    ]

    admin.add_views(*users_models)

    all_models = [
        WrapModelView(JobRecord, _db),
        WrapModelView(SettingRecord, _db),
    ]
    admin.add_views(*all_models)

    admin.add_view(
        WrapModelView(
            OwidChartTemplateView,
            _db,
            # name="Templates Need Update",
        )
    )


__all__ = [
    "add_admin_dashboard",
]
