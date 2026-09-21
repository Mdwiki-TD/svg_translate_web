"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

from .explorer_routes import ExplorerView
from .extract_routes import ExtractView
from .inject_routes import InjectView
from .owid_charts_routes import OwidChartsRoutes
from .routes import MainView
from .templates import TemplatesView
from .translate_routes import TranslateView

__all__ = [
    "MainView",
    "ExplorerView",
    "ExtractView",
    "InjectView",
    "OwidChartsRoutes",
    "TranslateView",
    "TemplatesView",
]
