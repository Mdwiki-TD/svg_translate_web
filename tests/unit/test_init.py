"""Tests for src/main_app/__init__.py - Flask application factory."""

from unittest.mock import patch

import pytest
from flask import Flask

from src.main_app import create_app
from src.main_app.config import TestingConfig


@pytest.fixture
def mock_environ(tmp_path):
    with patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": str(tmp_path / "test")}):
        yield


def test_create_app_basic(mock_environ):
    """Test create_app creates a Flask application."""
    app = create_app(TestingConfig)
    assert isinstance(app, Flask)
    assert app.secret_key is not None
    assert len(app.secret_key) > 0


def test_create_app_sets_session_cookie_config(mock_environ):
    """Test create_app sets session cookie configuration."""
    app = create_app(TestingConfig)

    assert "SESSION_COOKIE_HTTPONLY" in app.config
    assert "SESSION_COOKIE_SECURE" in app.config
    assert "SESSION_COOKIE_SAMESITE" in app.config


def test_create_app_jinja_filter_registered(mock_environ):
    """Test create_app registers the get_status_class Jinja filter."""
    app = create_app(TestingConfig)
    assert "get_status_class" in app.jinja_env.filters


def test_create_app_error_handlers(mock_environ):
    """Test create_app registers error handlers."""
    app = create_app(TestingConfig)

    # Test 404 error handler
    with app.test_request_context():
        error_handler_404 = app.error_handler_spec.get(None, {}).get(404)
        assert error_handler_404 is not None

    # Test 500 error handler
    with app.test_request_context():
        error_handler_500 = app.error_handler_spec.get(None, {}).get(500)
        assert error_handler_500 is not None


def test_create_app_404_handler(mock_environ):
    """Test the 404 error handler."""
    app = create_app(TestingConfig)
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/nonexistent-route-that-should-404")
        assert response.status_code == 404


def test_create_app_url_map_strict_slashes(mock_environ):
    """Test create_app disables strict slashes."""
    app = create_app(TestingConfig)
    assert app.url_map.strict_slashes is False


def test_create_app_template_folder(mock_environ):
    """Test create_app sets custom template folder."""
    app = create_app(TestingConfig)
    assert str(app.template_folder).endswith("templates")


def test_create_app_static_folder(mock_environ):
    """Test create_app sets custom static folder."""
    app = create_app(TestingConfig)
    assert str(app.static_folder).endswith("static")
