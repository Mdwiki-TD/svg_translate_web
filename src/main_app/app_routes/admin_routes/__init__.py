"""Admin blueprint package."""

from .coordinators import bp_coordinators
from .jobs import Jobs
from .owid_charts import OwidCharts
from .settings import SettingsRoutes
from .templates import Templates

__all__ = [
    "bp_coordinators",
    "Jobs",
    "OwidCharts",
    "SettingsRoutes",
    "Templates",
]
