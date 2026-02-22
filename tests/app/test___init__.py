"""Tests for src/app/__init__.py - Flask application factory."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from flask import Flask

from src.app import format_stage_timestamp, create_app


def test_format_stage_timestamp_valid():
    """Test format_stage_timestamp with valid ISO8601 timestamp."""
    result = format_stage_timestamp("2025-10-27T04:41:07")
    assert result == "Oct 27, 2025, 4:41 AM"


def test_format_stage_timestamp_afternoon():
    """Test format_stage_timestamp with afternoon time."""
    result = format_stage_timestamp("2025-10-27T14:30:00")
    assert result == "Oct 27, 2025, 2:30 PM"


def test_format_stage_timestamp_midnight():
    """Test format_stage_timestamp with midnight."""
    result = format_stage_timestamp("2025-10-27T00:00:00")
    assert result == "Oct 27, 2025, 12:00 AM"


def test_format_stage_timestamp_noon():
    """Test format_stage_timestamp with noon."""
    result = format_stage_timestamp("2025-10-27T12:00:00")
    assert result == "Oct 27, 2025, 12:00 PM"


def test_format_stage_timestamp_empty_string():
    """Test format_stage_timestamp with empty string."""
    result = format_stage_timestamp("")
    assert result == ""


def test_format_stage_timestamp_none():
    """Test format_stage_timestamp with None-like value."""
    result = format_stage_timestamp(None)
    assert result == ""


def test_format_stage_timestamp_invalid_format():
    """Test format_stage_timestamp with invalid timestamp format."""
    result = format_stage_timestamp("invalid-timestamp")
    assert result == ""


def test_format_stage_timestamp_with_microseconds():
    """Test format_stage_timestamp with microseconds."""
    result = format_stage_timestamp("2025-10-27T04:41:07.123456")
    assert result == "Oct 27, 2025, 4:41 AM"


def test_format_stage_timestamp_different_months():
    """Test format_stage_timestamp with different months."""
    assert "Jan" in format_stage_timestamp("2025-01-15T10:30:00")
    assert "Feb" in format_stage_timestamp("2025-02-15T10:30:00")
    assert "Dec" in format_stage_timestamp("2025-12-15T10:30:00")


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_basic():
    """Test create_app creates a Flask application."""
    app = create_app()
    assert isinstance(app, Flask)
    assert app.secret_key is not None
    assert len(app.secret_key) > 0


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_registers_blueprints():
    """Test create_app registers all blueprints."""
    app = create_app()

    # Check that blueprints are registered
    blueprint_names = [bp.name for bp in app.blueprints.values()]

    expected_blueprints = [
        'main',
        'tasks',
        'explorer',
        'templates',
        'tasks_managers',
        'admin',
        'auth',
        'fix_nested',
        'fix_nested_explorer',
        'extract'
    ]

    for bp_name in expected_blueprints:
        assert bp_name in blueprint_names, f"Blueprint {bp_name} not registered"


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_sets_session_cookie_config():
    """Test create_app sets session cookie configuration."""
    app = create_app()

    assert 'SESSION_COOKIE_HTTPONLY' in app.config
    assert 'SESSION_COOKIE_SECURE' in app.config
    assert 'SESSION_COOKIE_SAMESITE' in app.config


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_sets_use_mw_oauth():
    """Test create_app sets USE_MW_OAUTH config."""
    app = create_app()
    assert 'USE_MW_OAUTH' in app.config


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_jinja_filter_registered():
    """Test create_app registers the format_stage_timestamp Jinja filter."""
    app = create_app()
    assert 'format_stage_timestamp' in app.jinja_env.filters


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
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


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_404_handler():
    """Test the 404 error handler."""
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        response = client.get('/nonexistent-route-that-should-404')
        assert response.status_code == 404


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_url_map_strict_slashes():
    """Test create_app disables strict slashes."""
    app = create_app()
    assert app.url_map.strict_slashes is False


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_template_folder():
    """Test create_app sets custom template folder."""
    app = create_app()
    assert app.template_folder.endswith('templates')


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_static_folder():
    """Test create_app sets custom static folder."""
    app = create_app()
    assert app.static_folder.endswith('static')


@patch.dict('os.environ', {'FLASK_SECRET_KEY': 'test-secret', 'MAIN_DIR': '/tmp/test'})
def test_create_app_jinja_globals():
    """Test create_app sets Jinja globals."""
    app = create_app()
    assert 'USE_MW_OAUTH' in app.jinja_env.globals


def test_format_stage_timestamp_edge_time_values():
    """Test format_stage_timestamp with edge case time values."""
    # Test 11 AM (should show as 11 AM, not 11 PM)
    result = format_stage_timestamp("2025-10-27T11:00:00")
    assert result == "Oct 27, 2025, 11:00 AM"

    # Test 1 AM
    result = format_stage_timestamp("2025-10-27T01:00:00")
    assert result == "Oct 27, 2025, 1:00 AM"

    # Test 11 PM
    result = format_stage_timestamp("2025-10-27T23:00:00")
    assert result == "Oct 27, 2025, 11:00 PM"

    # Test 1 PM
    result = format_stage_timestamp("2025-10-27T13:00:00")
    assert result == "Oct 27, 2025, 1:00 PM"