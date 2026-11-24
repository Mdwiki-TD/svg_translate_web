"""
Flask routes factory.
"""

from __future__ import annotations

from .public.routes_utils import RequestContextHelper
from .routes_factory import RoutesFactory

__all__ = [
    "RequestContextHelper",
    "RoutesFactory",
]
