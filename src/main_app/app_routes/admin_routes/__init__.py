"""Admin blueprint package."""

from .coordinators import coordinators_module
from .jobs import bp_jobs
from .owid_charts import bp_owidcharts
from .settings import bp_settings
from .templates import bp_templates

__all__ = [
    "coordinators_module",
    "bp_jobs",
    "bp_owidcharts",
    "bp_settings",
    "bp_templates",
]
