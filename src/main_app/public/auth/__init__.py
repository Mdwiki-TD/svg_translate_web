"""Public auth package — routes and decorators."""

from __future__ import annotations

from .decorators import oauth_required
from .routes import AuthView

__all__ = [
    "oauth_required",
    "AuthView",
]
