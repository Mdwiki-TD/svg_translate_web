"""Regression tests for the Flask application factory."""

from __future__ import annotations

from importlib import reload

from src.app.db import svg_db
from src.app.config import DbConfig


def test_create_app_does_not_touch_mysql_when_unconfigured(monkeypatch):
    """Ensure the app factory can run without MySQL credentials."""

    # Reset any cached connection
    monkeypatch.setattr(svg_db, "_db", None)

    # Mock has_db_config to return False, preventing DB initialization
    monkeypatch.setattr(svg_db, "has_db_config", lambda: False)

    class _SentinelDatabase:
        def __init__(self, *_args, **_kwargs):  # pragma: no cover - defensive guard
            raise AssertionError("Database should not be instantiated during app creation")

    monkeypatch.setattr(svg_db, "Database", _SentinelDatabase)

    # Reload to ensure the latest configuration is used if the module was cached.
    import src.app as app_module

    reload(app_module)

    app = app_module.create_app()

    assert app is not None