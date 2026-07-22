"""
Defines the main routes for the application, such as the homepage.
"""

from __future__ import annotations

from .explorer_routes import ExplorerRoutes
from .extract_routes import ExtractRoutes
from .owid_charts_routes import OwidChartsRoutes
from .routes import MainRoutes

__all__ = [
    "MainRoutes",
    "ExplorerRoutes",
    "ExtractRoutes",
    "OwidChartsRoutes",
]
