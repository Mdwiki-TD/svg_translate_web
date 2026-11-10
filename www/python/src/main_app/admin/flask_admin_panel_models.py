"""Admin blueprint package."""

from dataclasses import dataclass, field
from typing import Any

from ..database.models import (
    AdminUserRecord,
    JobRecord,
    OwidChartRecord,
    OwidSlugRedirectRecord,
    SettingRecord,
    TemplateRecord,
    UserRecord,
)


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


__all__ = [
    "categories",
    "ModelItem",
]
