"""Regression tests for the Flask application factory."""

from __future__ import annotations

from importlib import reload

from src.main_app.db import svg_db


def test_create_app_does_not_touch_mysql_when_unconfigured(monkeypatch):
    """Ensure the app factory can run without MySQL credentials."""

    # Reset any cached connection and explicitly mark the configuration as empty.
    monkeypatch.setattr(svg_db, "_db", None)
    from src.main_app.config import DbConfig
    monkeypatch.setattr(svg_db, "settings", type(svg_db.settings)(
        **{
            **svg_db.settings.__dict__,
            "database_data": DbConfig(db_name="", db_host="", db_user=None, db_password=None)
        }
    ))

    class _SentinelDatabase:
        def __init__(self, *_args, **_kwargs):  # pragma: no cover - defensive guard
            raise AssertionError("Database should not be instantiated during app creation")

    monkeypatch.setattr(svg_db, "Database", _SentinelDatabase)

    # Reload to ensure the latest configuration is used if the module was cached.
    import src.main_app as app_module

    reload(app_module)

    app = app_module.create_app()

    assert app is not None


def test_format_stage_timestamp_valid():
    """Test format_stage_timestamp with valid timestamp."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("2025-10-27T04:41:07")

    assert "Oct 27, 2025" in result
    assert "4:41 AM" in result


def test_format_stage_timestamp_empty():
    """Test format_stage_timestamp with empty string."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("")

    assert result == ""


def test_format_stage_timestamp_invalid():
    """Test format_stage_timestamp with invalid timestamp."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("invalid-timestamp")

    assert result == ""


def test_format_stage_timestamp_afternoon():
    """Test format_stage_timestamp with PM time."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("2025-10-27T16:41:07")

    assert "Oct 27, 2025" in result
    assert "4:41 PM" in result


def test_format_stage_timestamp_noon():
    """Test format_stage_timestamp with noon."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("2025-10-27T12:00:00")

    assert "Oct 27, 2025" in result
    assert "12:00 PM" in result


def test_format_stage_timestamp_midnight():
    """Test format_stage_timestamp with midnight."""
    from src.main_app import format_stage_timestamp

    result = format_stage_timestamp("2025-10-27T00:00:00")

    assert "Oct 27, 2025" in result
    assert "12:00 AM" in result


def test_create_app_registers_blueprints(monkeypatch):
    """Test create_app registers all required blueprints."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app()

    # Check that blueprints are registered
    blueprint_names = [bp.name for bp in app.blueprints.values()]

    assert "main" in blueprint_names
    assert "tasks" in blueprint_names
    assert "explorer" in blueprint_names
    assert "templates" in blueprint_names
    assert "admin" in blueprint_names
    assert "auth" in blueprint_names
    assert "fix_nested" in blueprint_names
    assert "extract" in blueprint_names


def test_create_app_sets_secret_key(monkeypatch):
    """Test create_app sets the secret key from settings."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app()

    # Just verify a secret key is set
    assert app.secret_key is not None
    assert len(app.secret_key) > 0


def test_create_app_configures_cookie_settings(monkeypatch):
    """Test create_app configures cookie settings."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app()

    # Just verify cookie settings are configured
    assert "SESSION_COOKIE_HTTPONLY" in app.config
    assert "SESSION_COOKIE_SECURE" in app.config
    assert "SESSION_COOKIE_SAMESITE" in app.config


def test_create_app_sets_use_mw_oauth(monkeypatch):
    """Test create_app sets USE_MW_OAUTH config."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app()

    # Just verify USE_MW_OAUTH config is set
    assert "USE_MW_OAUTH" in app.config


def test_create_app_registers_context_processor(monkeypatch):
    """Test create_app registers context processor."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app()

    # The context processor should be registered
    assert len(app.template_context_processors[None]) > 0


def test_create_app_registers_error_handlers(monkeypatch):
    """Test create_app registers error handlers."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app()

    # Check that error handlers are registered
    assert 404 in app.error_handler_spec[None]
    assert 500 in app.error_handler_spec[None]


def test_create_app_strict_slashes_disabled(monkeypatch):
    """Test create_app disables strict slashes."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")

    from src.main_app import create_app

    app = create_app()

    assert app.url_map.strict_slashes is False


def test_create_app_jinja_env_configured(monkeypatch):
    """Test create_app configures Jinja environment."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret")
    monkeypatch.setenv("USE_MW_OAUTH", "true")

    from src.main_app import create_app
    from src.main_app.config import get_settings

    get_settings.cache_clear()
    app = create_app()

    # Check Jinja environment is configured
    assert "USE_MW_OAUTH" in app.jinja_env.globals
    assert "format_stage_timestamp" in app.jinja_env.filters

    get_settings.cache_clear()
