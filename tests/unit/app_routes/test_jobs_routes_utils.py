"""Tests for jobs_routes_utils ."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.main_app.app_routes.jobs_routes_utils import can_manage_job


class TestCanManageJob:
    def test_can_manage_job_none_user(self):
        """Test can_manage_job returns False when user is None."""
        job = MagicMock()
        job.username = "test_user"
        assert can_manage_job(job, None) is False

    def test_can_manage_job_admin(self):
        """Test can_manage_job returns True when user is admin (coordinator)."""
        job = MagicMock()
        job.username = "other_user"

        user = MagicMock()
        user.username = "admin_user"
        user.is_active_admin = True
        assert can_manage_job(job, user) is True

    def test_can_manage_job_owner(self):
        """Test can_manage_job returns True when user is job owner."""
        job = MagicMock()
        job.username = "owner_user"

        user = MagicMock()
        user.username = "owner_user"
        user.is_active_admin = False
        assert can_manage_job(job, user) is True

    def test_can_manage_job_not_owner_not_admin(self):
        """Test can_manage_job returns False when user is not owner and not admin."""
        job = MagicMock()
        job.username = "owner_user"

        user = MagicMock()
        user.username = "other_user"
        user.is_active_admin = False
        assert can_manage_job(job, user) is False

    def test_job_with_no_username(self):
        job = MagicMock()
        job.username = None
        user = MagicMock()
        user.username = "user"
        user.is_active_admin = False
        assert can_manage_job(job, user) is False

    def test_can_manage_job_no_job_username(self):
        """Test can_manage_job returns True for admin when job has no username."""
        job = MagicMock()
        job.username = None

        user = MagicMock()
        user.username = "admin"
        user.is_active_admin = True
        assert can_manage_job(job, user) is True
