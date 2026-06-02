"""Admin blueprint package."""

from .coordinators import coordinators_module
from .jobs import jobs_module
from .owid_charts import owidcharts_module
from .settings import settings_module
from .templates import templates_module

__all__ = [
    "coordinators_module",
    "jobs_module",
    "owidcharts_module",
    "settings_module",
    "templates_module",
]
