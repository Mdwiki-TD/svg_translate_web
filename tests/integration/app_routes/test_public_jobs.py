"""Tests for public_jobs routes."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.main_app.app_routes.public_jobs import JobsPublicRoutes, _can_manage_job


def test_can_manage_job_none_user():
    """Test _can_manage_job returns False when user is None."""
    job = MagicMock()
    job.username = "test_user"
    assert _can_manage_job(job, None) is False


def test_can_manage_job_admin():
    """Test _can_manage_job returns True when user is admin (coordinator)."""
    job = MagicMock()
    job.username = "other_user"

    user = MagicMock()
    user.username = "admin_user"
    user.is_active_admin = True
    assert _can_manage_job(job, user) is True


def test_can_manage_job_owner():
    """Test _can_manage_job returns True when user is job owner."""
    job = MagicMock()
    job.username = "owner_user"

    user = MagicMock()
    user.username = "owner_user"
    assert _can_manage_job(job, user) is True


def test_can_manage_job_not_owner_not_admin():
    """Test _can_manage_job returns False when user is not owner and not admin."""
    job = MagicMock()
    job.username = "owner_user"

    user = MagicMock()
    user.username = "other_user"
    user.is_active_admin = False
    assert _can_manage_job(job, user) is False


def test_can_manage_job_no_job_username():
    """Test _can_manage_job returns True for admin when job has no username."""
    job = MagicMock()
    job.username = None

    user = MagicMock()
    user.username = "admin"
    user.is_active_admin = True
    assert _can_manage_job(job, user) is True


class TestJobsPublicRoutesInit:
    """Test JobsPublicRoutes initialization and route registration."""


def test_client_key_with_forwarded_for(app_mock):
    """Test _client_key returns first forwarded IP."""
    from src.main_app.app_routes.auth.routes import _client_key

    with app_mock.test_request_context(headers={"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}):
        result = _client_key()
        assert result == "192.168.1.1"


def test_client_key_no_remote_addr(app_mock):
    """Test _client_key returns anonymous when no remote addr."""
    from src.main_app.app_routes.auth.routes import _client_key

    with app_mock.test_request_context():
        result = _client_key()
        assert result == "anonymous"
