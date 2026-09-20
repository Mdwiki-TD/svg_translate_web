"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

from .explorer_routes import ExplorerRoutes
from .extract_routes import ExtractView
from .inject_routes import InjectView
from .owid_charts_routes import OwidChartsRoutes
from .routes import MainRoutes
from .templates import TemplatesView
from .translate_routes import TranslateView

__all__ = [
    "MainRoutes",
    "ExplorerRoutes",
    "ExtractView",
    "InjectView",
    "OwidChartsRoutes",
    "TranslateView",
    "TemplatesView",
]
