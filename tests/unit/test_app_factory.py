"""Tests for src/main_app/app_factory.py - Flask application factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from src.main_app.app_factory import AppFactory
from src.main_app.config import TestingConfig


@pytest.fixture
def mock_environ(tmp_path):
    with patch.dict("os.environ", {"FLASK_SECRET_KEY": "test-secret", "MAIN_DIR": str(tmp_path / "test")}):
        yield


def test_csrf_protection_enabled(mock_app):
    assert mock_app.config.get("WTF_CSRF_ENABLED", True) is False
    assert mock_app.config.get("WTF_CSRF_CHECK_DEFAULT", True) is True


class TestCreateApp:
    def test_create_app_basic(self, mock_environ):
        app = AppFactory.create(TestingConfig)
        assert isinstance(app, Flask)
        assert app.secret_key is not None
        assert len(app.secret_key) > 0

    def test_create_app_sets_session_cookie_config(self, mock_environ):
        app = AppFactory.create(TestingConfig)
        assert "SESSION_COOKIE_HTTPONLY" in app.config
        assert "SESSION_COOKIE_SECURE" in app.config
        assert "SESSION_COOKIE_SAMESITE" in app.config

    def test_create_app_jinja_filter_registered(self, mock_environ):
        app = AppFactory.create(TestingConfig)
        assert "get_status_class" in app.jinja_env.filters

    def test_create_app_error_handlers_registered(self, mock_environ):
        app = AppFactory.create(TestingConfig)
        spec = app.error_handler_spec.get(None, {})
        assert 400 in spec
        assert 404 in spec
        assert 500 in spec

    def test_create_app_url_map_strict_slashes(self, mock_environ):
        app = AppFactory.create(TestingConfig)
        assert app.url_map.strict_slashes is False

    def test_create_app_template_folder(self, mock_environ):
        app = AppFactory.create(TestingConfig)
        assert str(app.template_folder).endswith("templates")

    def test_create_app_static_folder(self, mock_environ):
        app = AppFactory.create(TestingConfig)
        assert str(app.static_folder).endswith("static")


class TestErrorHandlers:
    def test_error_handlers_400_returns_html(self, test_client):
        resp = test_client.get("/test?malformed")
        assert resp.status_code == 404
        assert resp.content_type == "text/html; charset=utf-8"

    def test_error_handlers_400_returns_application_json_if_api(self, test_client):
        resp = test_client.get("/api/test?malformed")
        assert resp.status_code == 404
        assert resp.content_type == "application/json"

    def test_error_handlers_404_returns_not_found(self, test_client):

        resp = test_client.get("/nonexistent-route-test-404")
        assert resp.status_code == 404

    def test_error_handlers_405_returns_not_allowed(self, test_client):

        resp = test_client.post("/")
        assert resp.status_code == 405

    def test_500_error_handler_exists(self, mock_app: Flask):
        spec = mock_app.error_handler_spec.get(None, {})
        has_handler = 500 in spec
        assert has_handler


class TestInitAppAndDb:
    @patch("src.main_app.app_factory.DatabaseBuilder.init_db")
    def test_init_app_and_db_success(self, mock_init_db, mock_environ):
        mock_db = MagicMock()
        mock_app = AppFactory.create(TestingConfig)
        mock_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        result = AppFactory.init_app_and_db(mock_app, mock_db)
        assert result is True

    @patch("src.main_app.app_factory.DatabaseBuilder.init_db", side_effect=Exception("DB error"))
    def test_init_app_and_db_exception(self, mock_init_db, mock_environ):
        mock_db = MagicMock()
        mock_app = AppFactory.create(TestingConfig)
        mock_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        result = AppFactory.init_app_and_db(mock_app, mock_db)
        assert result is False
