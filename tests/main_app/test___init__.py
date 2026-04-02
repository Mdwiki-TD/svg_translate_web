"""Tests for src/main_app/__init__.py - Flask application factory."""

from unittest.mock import patch

from flask import Flask

from src.main_app import create_app


@patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": "/tmp/test"})
def test_create_app_basic():
    """Test create_app creates a Flask application."""
    app = create_app()
    assert isinstance(app, Flask)
    assert app.secret_key is not None
    assert len(app.secret_key) > 0


@patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": "/tmp/test"})
def test_create_app_sets_session_cookie_config():
    """Test create_app sets session cookie configuration."""
    app = create_app()

    assert "SESSION_COOKIE_HTTPONLY" in app.config
    assert "SESSION_COOKIE_SECURE" in app.config
    assert "SESSION_COOKIE_SAMESITE" in app.config


@patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": "/tmp/test"})
def test_create_app_jinja_filter_registered():
    """Test create_app registers the format_stage_timestamp Jinja filter."""
    app = create_app()
    assert "format_stage_timestamp" in app.jinja_env.filters


@patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": "/tmp/test"})
def test_create_app_error_handlers():
    """Test create_app registers error handlers."""
    app = create_app()

    # Test 404 error handler
    with app.test_request_context():
        error_handler_404 = app.error_handler_spec.get(None, {}).get(404)
        assert error_handler_404 is not None

    # Test 500 error handler
    with app.test_request_context():
        error_handler_500 = app.error_handler_spec.get(None, {}).get(500)
        assert error_handler_500 is not None


@patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": "/tmp/test"})
def test_create_app_404_handler():
    """Test the 404 error handler."""
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/nonexistent-route-that-should-404")
        assert response.status_code == 404


@patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": "/tmp/test"})
def test_create_app_url_map_strict_slashes():
    """Test create_app disables strict slashes."""
    app = create_app()
    assert app.url_map.strict_slashes is False


@patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": "/tmp/test"})
def test_create_app_template_folder():
    """Test create_app sets custom template folder."""
    app = create_app()
    assert app.template_folder.endswith("templates")


@patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": "/tmp/test"})
def test_create_app_static_folder():
    """Test create_app sets custom static folder."""
    app = create_app()
    assert app.static_folder.endswith("static")
