"""
Unit tests for src/main_app/config/flask_config.py module.

Classes to test: Config, DevelopmentConfig, ProductionConfig, TestingConfig
"""

from __future__ import annotations

from src.main_app.config.flask_config import (
    Config,
    DevelopmentConfig,
    ProductionConfig,
    TestingConfig,
)


class TestTestingConfig:
    def test_testing_flag_true(self):
        assert TestingConfig.TESTING is True

    def test_debug_flag_false(self):
        assert TestingConfig.DEBUG is False

    def test_csrf_disabled(self):
        assert TestingConfig.WTF_CSRF_ENABLED is False

    def test_sqlite_in_memory(self):
        assert TestingConfig.SQLALCHEMY_DATABASE_URI == "sqlite:///:memory:"

    def test_secure_cookie_disabled(self):
        assert TestingConfig.SESSION_COOKIE_SECURE is False

    def test_secret_key_is_fixed(self):
        assert TestingConfig.SECRET_KEY == "test-secret-key-not-for-production"

    def test_not_collected_by_pytest(self):
        assert TestingConfig.__test__ is False


class TestDevelopmentConfig:
    def test_debug_enabled(self):
        assert DevelopmentConfig.DEBUG is True

    def test_testing_enabled(self):
        assert DevelopmentConfig.TESTING is True

    def test_cors_disabled(self):
        assert DevelopmentConfig.CORS_DISABLED is True

    def test_session_cookies_secure(self):
        assert DevelopmentConfig.SESSION_COOKIE_SECURE is True


class TestProductionConfig:
    def test_session_cookies_secure(self):
        assert ProductionConfig.SESSION_COOKIE_SECURE is True

    def test_session_httponly(self):
        assert ProductionConfig.SESSION_COOKIE_HTTPONLY is True

    def test_samesite_lax(self):
        assert ProductionConfig.SESSION_COOKIE_SAMESITE == "Lax"

    def test_cors_not_disabled(self):
        assert ProductionConfig.CORS_DISABLED is False


class TestConfig:
    def test_config_has_csrf_methods(self):
        assert "POST" in Config.WTF_CSRF_METHODS
        assert "PUT" in Config.WTF_CSRF_METHODS
        assert "PATCH" in Config.WTF_CSRF_METHODS
        assert "DELETE" in Config.WTF_CSRF_METHODS

    def test_config_has_csrf_headers(self):
        assert "X-CSRFToken" in Config.WTF_CSRF_HEADERS
        assert "X-CSRF-Token" in Config.WTF_CSRF_HEADERS

    def test_config_track_modifications_false(self):
        assert Config.SQLALCHEMY_TRACK_MODIFICATIONS is False
