"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

from .explorer_routes import ExplorerRoutes
from .extract_routes import ExtractRoutes
from .inject_routes import InjectRoutes
from .owid_charts_routes import OwidChartsRoutes
from .routes import MainRoutes
from .translate_routes import TranslateRoutes

__all__ = [
    "MainRoutes",
    "ExplorerRoutes",
    "ExtractRoutes",
    "InjectRoutes",
    "OwidChartsRoutes",
    "TranslateRoutes",
]
