"""Admin/Coordinator blueprint package."""

from __future__ import annotations

from .admins import AdminView
from .error_logs import CheckErrorLogsView
from .errors_route import CheckErrorsView
from .owid_charts import OwidChartsRoutes
from .settings import SettingsRoutes
from .slug_redirects import SlugRedirectsRoutes
from .templates import TemplatesRoutes
from .toolforge_jobs_view import ToolforgeJobsView
from .users import UsersRoutes

__all__ = [
    "AdminView",
    "CheckErrorLogsView",
    "CheckErrorsView",
    "OwidChartsRoutes",
    "SettingsRoutes",
    "SlugRedirectsRoutes",
    "TemplatesRoutes",
    "ToolforgeJobsView",
    "UsersRoutes",
]
