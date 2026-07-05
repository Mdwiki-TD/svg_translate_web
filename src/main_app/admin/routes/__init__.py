"""Admin blueprint package."""

from .coordinators import CoordinatorsRoutes
from .jobs import jobs_module
from .owid_charts import OwidChartsRoutes
from .settings import SettingsRoutes
from .slug_redirects import slug_redirects_module
from .templates import Templates
from .users import UsersRoutes

__all__ = [
    "CoordinatorsRoutes",
    "jobs_module",
    "OwidChartsRoutes",
    "slug_redirects_module",
    "SettingsRoutes",
    "Templates",
    "UsersRoutes",
]
