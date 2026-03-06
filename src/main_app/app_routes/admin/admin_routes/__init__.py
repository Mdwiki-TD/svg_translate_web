"""Admin blueprint package."""

from .coordinators import Coordinators
from .jobs import Jobs
from .recent import Recent
from .schedulers import Schedulers
from .settings import SettingsRoutes
from .templates import Templates

__all__ = [
    "Coordinators",
    "Jobs",
    "Recent",
    "Schedulers",
    "SettingsRoutes",
    "Templates",
]
