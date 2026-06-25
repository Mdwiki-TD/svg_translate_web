"""
Flask extensions initialization.

This module centralizes Flask extensions to prevent circular imports
and enable proper initialization order with the application factory pattern.

IMPORT RULE: Always import extensions from this module.
Never instantiate extensions elsewhere.

Usage:
    from main_app.shared.core.extensions import db, migrate, csrf
"""

from __future__ import annotations

from flask_migrate import Migrate

from ..db.exceptions import UniqueError
from ._csrf import (
    csrf,
    csrf_init_app,
)
from .data_base import (
    BaseModel,
    db,
)

# Flask-Migrate instance (Alembic integration)
migrate = Migrate()


__all__ = [
    "db",
    "BaseModel",
    "migrate",
    "csrf",
    "csrf_init_app",
    "UniqueError",
]
