"""Unit tests for create_owid_pages/worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.runner import (
    create_owid_pages_for_templates,
)


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

    def test_entry_point_creates_worker_and_runs(self, mock_services, mock_run):
        """Test that create_owid_pages_for_templates creates worker and runs it."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = []

        create_owid_pages_for_templates(job_id=1, user={"username": "test"})

        mock_run.assert_called_once()

    def test_entry_point_with_cancel_event(self, mock_services, mock_run):
        """Test entry point with cancel event."""
        cancel_event = threading.Event()

        create_owid_pages_for_templates(job_id=1, user=None, cancel_event=cancel_event)

        mock_run.assert_called_once()

    def test_entry_point_accepts_args_keyword_param(self, mock_services, mock_run):
        """Test that the entry point accepts args= keyword-only param (unified signature)."""
        # Should not raise TypeError; args is accepted but unused
        create_owid_pages_for_templates(job_id=1, user=None, args={"some_key": "value"})

        mock_run.assert_called_once()

    def test_entry_point_args_defaults_to_none(self, mock_services, mock_run):
        """Test that args defaults to None and the entry point works without it."""
        create_owid_pages_for_templates(job_id=99, user=None)

        mock_run.assert_called_once()

    def test_entry_point_maps_create_owid_pages_limit_to_limit_items(self, mock_services, mock_init, mock_run):
        """Test that limit_items is mapped to limit_items in args."""
        create_owid_pages_for_templates(
            job_id=1,
            user=None,
            args={"limit_items": 5},
        )

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["args"]["limit_items"] == 5

    def test_entry_point_does_not_map_when_key_absent(self, mock_services, mock_init, mock_run):
        """Test that args are passed unchanged when limit_items is absent."""
        create_owid_pages_for_templates(
            job_id=1,
            user=None,
            args={"other_key": "value"},
        )

        call_kwargs = mock_init.call_args.kwargs
        assert "limit_items" not in call_kwargs["args"]

    def test_entry_point_does_not_modify_args_when_args_is_none(self, mock_services, mock_init, mock_run):
        """Test that entry point works correctly when args is None."""
        create_owid_pages_for_templates(job_id=1, user=None, args=None)

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["args"] is None
