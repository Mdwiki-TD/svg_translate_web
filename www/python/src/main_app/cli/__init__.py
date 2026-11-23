"""
Flask application factory.
"""

from __future__ import annotations

import logging

from flask import Flask

from .cli_jobs import register_cli_jobs

logger = logging.getLogger(__name__)


class CliFactory:
    @classmethod
    def register(cls, app: Flask) -> None:
        register_cli_jobs(app)


__all__ = [
    "CliFactory",
]
