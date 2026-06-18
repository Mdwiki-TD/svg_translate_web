"""Tests for public_jobs routes."""

from __future__ import annotations

from src.main_app.app_routes.public_jobs import JobsPublicRoutes  # noqa: F401


class TestJobsPublicRoutesInit:
    """Test JobsPublicRoutes initialization and route registration."""


def test_client_key_with_forwarded_for(mock_app):
    """Test _client_key returns first forwarded IP."""
    from src.main_app.app_routes.auth.routes import _client_key

    with mock_app.test_request_context(headers={"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}):
        result = _client_key()
        assert result == "192.168.1.1"


def test_client_key_no_remote_addr(mock_app):
    """Test _client_key returns anonymous when no remote addr."""
    from src.main_app.app_routes.auth.routes import _client_key

    with mock_app.test_request_context():
        result = _client_key()
        assert result == "anonymous"
