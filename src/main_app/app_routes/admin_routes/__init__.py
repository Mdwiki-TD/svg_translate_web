"""Admin blueprint package."""

from .coordinators import bp_coordinators
from .jobs import bp_jobs
from .owid_charts import bp_owidcharts
from .settings import bp_settings
from .templates import bp_templates

__all__ = [
    "bp_coordinators",
    "bp_jobs",
    "bp_owidcharts",
    "bp_settings",
    "bp_templates",
]
