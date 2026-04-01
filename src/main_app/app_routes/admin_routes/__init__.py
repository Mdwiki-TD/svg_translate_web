"""Admin blueprint package."""

from .coordinators import Coordinators
from .jobs import Jobs
from .owid_charts import OwidCharts
from .recent import Recent
from .settings import SettingsRoutes
from .templates import Templates

__all__ = [
    "Coordinators",
    "Jobs",
    "OwidCharts",
    "Recent",
    "SettingsRoutes",
    "Templates",
]
