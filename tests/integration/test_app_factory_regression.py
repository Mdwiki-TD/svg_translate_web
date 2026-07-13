"""Integration tests for the Flask application factory."""

from __future__ import annotations

from importlib import reload
from unittest.mock import patch

import pytest

from src.main_app.config import TestingConfig


def test_create_app_does_not_touch_mysql_when_unconfigured(monkeypatch):
    """Ensure the app factory can run without MySQL credentials."""

    import src.main_app as app_module

    reload(app_module)

    app = app_module.create_app(TestingConfig)

    assert app is not None


@pytest.fixture
def mock_environ(tmp_path):
    with patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": str(tmp_path / "test")}):
        yield


def test_create_app_registers_blueprints(mock_environ):
    """Test create_app registers all blueprints."""
    from src.main_app import create_app

    app = create_app(TestingConfig)

    blueprint_names = [bp.name for bp in app.blueprints.values()]

    expected_blueprints = [
        "main",
        "public_jobs",
        "explorer",
        "adminpanel",
        "auth",
        "extract",
    ]

    for bp_name in expected_blueprints:
        assert bp_name in blueprint_names, f"Blueprint {bp_name} not registered"


def test_create_app_sets_secret_key(monkeypatch):
    """Test create_app sets the secret key from settings."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app(TestingConfig)

    assert app.secret_key is not None
    assert len(app.secret_key) > 0


def test_create_app_configures_cookie_settings(monkeypatch):
    """Test create_app configures cookie settings."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app(TestingConfig)

    assert "SESSION_COOKIE_HTTPONLY" in app.config
    assert "SESSION_COOKIE_SECURE" in app.config
    assert "SESSION_COOKIE_SAMESITE" in app.config


def test_create_app_registers_context_processor(monkeypatch):
    """Test create_app registers context processor."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app(TestingConfig)

    assert len(app.template_context_processors[None]) > 0


def test_create_app_registers_error_handlers(monkeypatch):
    """Test create_app registers error handlers."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app(TestingConfig)

    assert 404 in app.error_handler_spec[None]
    assert 500 in app.error_handler_spec[None]


def test_create_app_strict_slashes_disabled(monkeypatch):
    """Test create_app disables strict slashes."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app(TestingConfig)

    assert app.url_map.strict_slashes is False


def test_create_app_jinja_env_configured(monkeypatch):
    """Test create_app configures Jinja environment."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app
    from src.main_app.config.main_settings import get_settings

    get_settings.cache_clear()
    app = create_app(TestingConfig)

    assert "short_url" in app.jinja_env.filters

    get_settings.cache_clear()
