"""Admin blueprint package."""

from .coordinators import CoordinatorsRoutes
from .jobs import AdminJobsRoutes
from .owid_charts import OwidChartsRoutes
from .settings import SettingsRoutes
from .slug_redirects import SlugRedirects
from .templates import Templates
from .users import UsersRoutes

__all__ = [
    "CoordinatorsRoutes",
    "AdminJobsRoutes",
    "OwidChartsRoutes",
    "SlugRedirects",
    "SettingsRoutes",
    "Templates",
    "UsersRoutes",
]
