"""Tests for public_jobs routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.app_routes.public_jobs import JobsPublicRoutes, _can_manage_job


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    return app


def test_can_manage_job_none_user():
    """Test _can_manage_job returns False when user is None."""
    job = MagicMock()
    job.username = "test_user"
    assert _can_manage_job(job, None) is False


def test_can_manage_job_admin():
    """Test _can_manage_job returns True when user is admin (coordinator)."""
    job = MagicMock()
    job.username = "other_user"

    with patch("src.main_app.app_routes.public_jobs.active_coordinators", return_value=["admin_user", "coordinator"]):
        user = MagicMock()
        user.username = "admin_user"
        assert _can_manage_job(job, user) is True


def test_can_manage_job_owner():
    """Test _can_manage_job returns True when user is job owner."""
    job = MagicMock()
    job.username = "owner_user"

    with patch("src.main_app.app_routes.public_jobs.active_coordinators", return_value=["admin"]):
        user = MagicMock()
        user.username = "owner_user"
        assert _can_manage_job(job, user) is True


def test_can_manage_job_not_owner_not_admin():
    """Test _can_manage_job returns False when user is not owner and not admin."""
    job = MagicMock()
    job.username = "owner_user"

    with patch("src.main_app.app_routes.public_jobs.active_coordinators", return_value=["admin"]):
        user = MagicMock()
        user.username = "other_user"
        assert _can_manage_job(job, user) is False


def test_can_manage_job_no_job_username():
    """Test _can_manage_job returns True for admin when job has no username."""
    job = MagicMock()
    job.username = None

    with patch("src.main_app.app_routes.public_jobs.active_coordinators", return_value=["admin"]):
        user = MagicMock()
        user.username = "admin"
        assert _can_manage_job(job, user) is True


class TestJobsPublicRoutesInit:
    """Test JobsPublicRoutes initialization and route registration."""

    def test_registers_all_routes(self):
        """Test JobsPublicRoutes registers expected number of routes."""
        mock_bp = MagicMock()

        JobsPublicRoutes(mock_bp)

        assert mock_bp.post.call_count == 4  # cancel, delete, start, start_with_args
        assert mock_bp.get.call_count >= 8  # list, detail, download, crop, etc.

    def test_registers_cancel_job_route(self):
        """Test cancel job route is registered."""
        mock_bp = MagicMock()
        JobsPublicRoutes(mock_bp)

        mock_bp.post.assert_any_call("/<string:job_type>/<int:job_id>/cancel")

    def test_registers_jobs_list_route(self):
        """Test jobs list route is registered."""
        mock_bp = MagicMock()
        JobsPublicRoutes(mock_bp)

        mock_bp.get.assert_any_call("/<string:job_type>/list")

    def test_registers_job_detail_route(self):
        """Test job detail route is registered."""
        mock_bp = MagicMock()
        JobsPublicRoutes(mock_bp)

        mock_bp.get.assert_any_call("/<string:job_type>/<int:job_id>")

    def test_registers_start_job_route(self):
        """Test start job route is registered."""
        mock_bp = MagicMock()
        JobsPublicRoutes(mock_bp)

        mock_bp.post.assert_any_call("/<string:job_type>/start")

    def test_registers_delete_job_route(self):
        """Test delete job route is registered."""
        mock_bp = MagicMock()
        JobsPublicRoutes(mock_bp)

        mock_bp.post.assert_any_call("/<string:job_type>/<int:job_id>/delete")


def test_client_key_with_forwarded_for(app):
    """Test _client_key returns first forwarded IP."""
    from src.main_app.app_routes.auth.routes import _client_key

    with app.test_request_context(headers={"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}):
        result = _client_key()
        assert result == "192.168.1.1"


def test_client_key_no_remote_addr(app):
    """Test _client_key returns anonymous when no remote addr."""
    from src.main_app.app_routes.auth.routes import _client_key

    with app.test_request_context():
        result = _client_key()
        assert result == "anonymous"
