"""Tests for src/main_app/__init__.py - Flask application factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app import register_error_pages  # noqa: F401
from src.main_app import create_app, init_app_and_db
from src.main_app.config import TestingConfig


@pytest.fixture
def mock_environ(tmp_path):
    with patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": str(tmp_path / "test")}):
        yield


@pytest.fixture
def app(mock_environ):
    return create_app(TestingConfig)


def test_csrf_protection_enabled(app):
    assert app.config.get("WTF_CSRF_ENABLED", True) is False
    assert app.config.get("WTF_CSRF_CHECK_DEFAULT", True) is True


class TestCreateApp:
    def test_create_app_basic(self, mock_environ):
        app = create_app(TestingConfig)
        assert isinstance(app, Flask)
        assert app.secret_key is not None
        assert len(app.secret_key) > 0

    def test_create_app_sets_session_cookie_config(self, mock_environ):
        app = create_app(TestingConfig)
        assert "SESSION_COOKIE_HTTPONLY" in app.config
        assert "SESSION_COOKIE_SECURE" in app.config
        assert "SESSION_COOKIE_SAMESITE" in app.config

    def test_create_app_jinja_filter_registered(self, mock_environ):
        app = create_app(TestingConfig)
        assert "get_status_class" in app.jinja_env.filters

    def test_create_app_error_handlers_registered(self, mock_environ):
        app = create_app(TestingConfig)
        spec = app.error_handler_spec.get(None, {})
        assert 400 in spec
        assert 404 in spec
        assert 500 in spec

    def test_create_app_url_map_strict_slashes(self, mock_environ):
        app = create_app(TestingConfig)
        assert app.url_map.strict_slashes is False

    def test_create_app_template_folder(self, mock_environ):
        app = create_app(TestingConfig)
        assert str(app.template_folder).endswith("templates")

    def test_create_app_static_folder(self, mock_environ):
        app = create_app(TestingConfig)
        assert str(app.static_folder).endswith("static")

    def test_create_app_none_config_raises(self, mock_environ):
        with pytest.raises(ValueError, match="config_class must be provided"):
            create_app(None)


class TestErrorHandlers:

    def test_error_handlers_400_returns_html(self, app):
        with app.test_client() as client:
            resp = client.get("/test?malformed")
            assert resp.status_code == 404
            assert resp.content_type == "text/html; charset=utf-8"

    def test_error_handlers_400_returns_application_json_if_api(self, app):
        with app.test_client() as client:
            resp = client.get("/api/test?malformed")
            assert resp.status_code == 404
            assert resp.content_type == "application/json"

    def test_error_handlers_404_returns_not_found(self, app):
        with app.test_client() as client:
            resp = client.get("/nonexistent-route-test-404")
            assert resp.status_code == 404

    def test_error_handlers_405_returns_not_allowed(self, app):
        with app.test_client() as client:
            resp = client.post("/")
            assert resp.status_code == 405

    def test_500_error_handler_exists(self, app):
        spec = app.error_handler_spec.get(None, {})
        has_handler = 500 in spec
        assert has_handler


class TestInitAppAndDb:

    @patch("src.main_app.init_db")
    def test_init_app_and_db_success(self, mock_init_db, mock_environ):
        mock_db = MagicMock()
        mock_app = create_app(TestingConfig)
        mock_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        result = init_app_and_db(mock_app, mock_db)
        assert result is True

    @patch("src.main_app.init_db", side_effect=Exception("DB error"))
    def test_init_app_and_db_exception(self, mock_init_db, mock_environ):
        mock_db = MagicMock()
        mock_app = create_app(TestingConfig)
        mock_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        result = init_app_and_db(mock_app, mock_db)
        assert result is False
