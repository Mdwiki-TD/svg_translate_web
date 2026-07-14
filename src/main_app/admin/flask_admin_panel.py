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


class MyView(BaseView):
    @expose("/")
    def index(self):
        return "Hello World!"


def add_admin_dashboard(app: Flask, _db) -> None:
    # Initialize Admin and add views
    theme = Bootstrap4Theme(
        # base_template="admin/index.html",
        swatch="default",
    )
    admin = Admin(app, name="microblog", theme=theme)

    admin.add_category(
        name="Main",
        class_name=None,
        icon_type=None,
        icon_value=None,
    )

    main_models = [
        ModelView(TemplateRecord, _db, category="Main"),
        ModelView(TemplateNeedUpdateView, _db, name="Templates Need Update", category="Main"),
        ModelView(OwidChartRecord, _db, category="Main", name="OWID Charts"),
        ModelView(OwidSlugRedirectRecord, _db, category="Main"),
    ]
    admin.add_views(*main_models)

    admin.add_category(
        name="Users",
        class_name=None,
        icon_type=None,
        icon_value=None,
    )

    users_models = [
        ModelView(AdminUserRecord, _db, category="Users"),
        ModelView(UserRecord, _db, category="Users"),
    ]

    admin.add_views(*users_models)

    all_models = [
        ModelView(JobRecord, _db),
        ModelView(SettingRecord, _db),
    ]
    admin.add_views(*all_models)

    admin.add_view(
        ModelView(
            OwidChartTemplateView,
            _db,
            # name="Templates Need Update",
        )
    )

    """
    admin.add_view(
        MyView(
            name='My View', menu_icon_type='glyph', menu_icon_value='glyphicon-home', category="category"
        )
    )
    """


__all__ = [
    "add_admin_dashboard",
]
