"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

from .api_routes import ApiRoutes
from .auth_route import AuthView
from .explorer_routes import ExplorerView
from .extract_routes import ExtractView
from .inject_routes import InjectView
from .jobs_utils_bp import UtilsJobsBpRoutes
from .main_route import MainView
from .owid_charts_routes import OwidChartsRoutes
from .profile_view import ProfileView
from .templates_view import TemplatesView
from .translate_routes import TranslateView

__all__ = [
    "MainView",
    "ProfileView",
    "ExplorerView",
    "ExtractView",
    "InjectView",
    "OwidChartsRoutes",
    "TranslateView",
    "TemplatesView",
    "ApiRoutes",
    "AuthView",
    "UtilsJobsBpRoutes",
]
