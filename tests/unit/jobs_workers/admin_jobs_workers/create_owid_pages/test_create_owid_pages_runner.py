"""Unit tests for create_owid_pages/worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.runner import (
    create_owid_pages_for_templates,
)
from src.main_app.jobs_workers.objects import JobsRunner


@pytest.fixture
def mock_run():
    with patch("src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.CreateOwidPagesWorker.run") as mock:
        mock.return_value = {"status": "completed"}
        yield mock


@pytest.fixture
def mock_init():
    with patch(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.CreateOwidPagesWorker.__init__",
        return_value=None,
    ) as mock:
        yield mock


class TestCreateOwidPagesForTemplates:
    """Tests for create_owid_pages_for_templates entry point."""

    def test_entry_point_creates_worker_and_runs(self, mock_owid_pages_services, mock_run):
        """Test that create_owid_pages_for_templates creates worker and runs it."""
        mock_owid_pages_services["get_user_site"].return_value = MagicMock()
        mock_owid_pages_services["list"].return_value = []

        runner_data = JobsRunner(job_id=1, user={"username": "test"})
        create_owid_pages_for_templates(runner_data)

        mock_run.assert_called_once()

    def test_entry_point_with_cancel_event(self, mock_owid_pages_services, mock_run):
        """Test entry point with cancel event."""
        cancel_event = threading.Event()

        runner_data = JobsRunner(job_id=1, user={}, cancel_event=cancel_event)
        create_owid_pages_for_templates(runner_data)

        mock_run.assert_called_once()

    def test_entry_point_accepts_args_keyword_param(self, mock_owid_pages_services, mock_run):
        """Test that the entry point accepts args= keyword-only param (unified signature)."""
        # Should not raise TypeError; args is accepted but unused
        runner_data = JobsRunner(job_id=1, user={}, args={"some_key": "value"})
        create_owid_pages_for_templates(runner_data)

        mock_run.assert_called_once()

    def test_entry_point_args_defaults_to_none(self, mock_owid_pages_services, mock_run):
        """Test that args defaults to None and the entry point works without it."""
        runner_data = JobsRunner(job_id=99, user={})
        create_owid_pages_for_templates(runner_data)

        mock_run.assert_called_once()

    def test_entry_point_maps_create_owid_pages_limit_to_limit_items(
        self, mock_owid_pages_services, mock_init, mock_run
    ):
        """Test that limit_items is mapped to limit_items in args."""
        runner_data = JobsRunner(job_id=1, user={}, args={"limit_items": 5})
        create_owid_pages_for_templates(runner_data)

        call_args = mock_init.call_args[0]
        assert call_args == (runner_data,)
        assert call_args[0].args["limit_items"] == 5

    def test_entry_point_does_not_map_when_key_absent(self, mock_owid_pages_services, mock_init, mock_run):
        """Test that args are passed unchanged when limit_items is absent."""
        runner_data = JobsRunner(job_id=1, user={}, args={"other_key": "value"})
        create_owid_pages_for_templates(runner_data)

        call_args = mock_init.call_args[0]
        assert call_args == (runner_data,)
        assert "limit_items" not in call_args[0].args

    def test_entry_point_does_not_modify_args_when_args_is_none(self, mock_owid_pages_services, mock_init, mock_run):
        """Test that entry point works correctly when args is None."""
        runner_data = JobsRunner(job_id=1, user={}, args=None)
        create_owid_pages_for_templates(runner_data)

        call_args = mock_init.call_args[0]
        assert call_args == (runner_data,)
        assert call_args[0].args is None
