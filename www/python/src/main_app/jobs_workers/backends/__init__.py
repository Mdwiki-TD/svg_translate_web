"""Job execution backends (thread / toolforge)."""

from __future__ import annotations

from .base import JobBackend
from .registry import get_backend, get_backend_name

__all__ = [
    "JobBackend",
    "get_backend",
    "get_backend_name",
]
