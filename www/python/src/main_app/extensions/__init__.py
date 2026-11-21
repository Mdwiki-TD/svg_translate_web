"""
Flask extensions initialization.

This module centralizes Flask extensions to prevent circular imports
and enable proper initialization order with the application factory pattern.

IMPORT RULE: Always import extensions from this module.
Never instantiate extensions elsewhere.
"""

from __future__ import annotations

from flask_migrate import Migrate

from .csrf_protect import (
    csrf,
    csrf_exempt,
    csrf_init_app,
)

# Flask-Migrate instance (Alembic integration)
migrate = Migrate()

__all__ = [
    "migrate",
    "csrf",
    "csrf_init_app",
    "csrf_exempt",
]
