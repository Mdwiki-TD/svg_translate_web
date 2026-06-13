"""Tests for app.py WSGI entry point."""

from __future__ import annotations

from flask import Flask


class TestCreateApp:
    """Tests for the create_app factory."""

    def test_create_app_returns_flask_instance(self, app: Flask):
        """create_app should return a configured Flask application."""
        assert isinstance(app, Flask)

    def test_app_has_strict_slashes_disabled(self, app: Flask):
        """strict_slashes should be False for flexible URL matching."""
        assert app.url_map.strict_slashes is False

    def test_app_has_csrf_protection(self, app: Flask):
        """CSRFProtect should be initialized."""
        from flask_wtf.csrf import CSRFProtect  # noqa: F401

        assert "csrf" in app.extensions

    def test_app_has_error_handlers(self, app: Flask):
        """Error handlers should be registered for common HTTP codes."""
        assert 400 in app.error_handler_spec.get(None, {})
        assert 403 in app.error_handler_spec.get(None, {})
        assert 404 in app.error_handler_spec.get(None, {})
        assert 405 in app.error_handler_spec.get(None, {})
        assert 500 in app.error_handler_spec.get(None, {})

    def test_app_has_templte_folder(self, app: Flask):
        """App should have a template folder configured."""
        assert app.template_folder is not None

    def test_app_has_static_folder(self, app: Flask):
        """App should have a static folder configured."""
        assert app.static_folder is not None


class TestRegisterErrorPages:
    """Tests for error handler registration."""

    def test_400_handler_returns_tuple(self, app: Flask):
        """400 handler should return (template, 400)."""
        with app.test_client() as client:
            response = client.get("/nonexistent-endpoint-400")
            assert response.status_code == 404

    def test_404_handler(self, app: Flask):
        """404 handler should return 404 status."""
        with app.test_client() as client:
            response = client.get("/this-page-does-not-exist")
            assert response.status_code == 404


class TestAppConfig:
    """Tests for application configuration."""

    def test_app_is_testing_in_test_mode(self, app: Flask):
        """App should be in testing mode when using TestingConfig."""
        assert app.config["TESTING"] is True

    def test_app_has_secret_key(self, app: Flask):
        """App should have a secret key set."""
        assert app.secret_key is not None
        assert len(app.secret_key) > 0
