"""
Flask routes factory.
"""

from __future__ import annotations

import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from ..admin import AdminsRouteRegister
from ..public import PublicRouteRegister

logger = logging.getLogger(__name__)


class RoutesFactory:
    @classmethod
    def register(cls, app: Flask, _db: SQLAlchemy) -> None:
        PublicRouteRegister.register(app)
        AdminsRouteRegister.register(app, _db)


__all__ = [
    "RoutesFactory",
]
