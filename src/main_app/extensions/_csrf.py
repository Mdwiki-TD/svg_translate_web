""" """

from __future__ import annotations

import logging

from flask import Flask
from flask_wtf.csrf import CSRFProtect

logger = logging.getLogger(__name__)

# CSRF Protection
csrf = CSRFProtect()


def csrf_init_app(app: Flask) -> None:
    """Initialize CSRF protection."""
    csrf.init_app(app)


__all__ = [
    "csrf",
    "csrf_init_app",
]
