"""Unit tests for update_owid_charts/runner module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.runner import (
    update_owid_charts_worker_entry,
)


class TestUpdateOwidChartsWorkerEntry:
    """Tests for update_owid_charts_worker_entry entry point."""

    def test_entry_point_creates_worker_and_runs(self):
        """Test that entry point creates worker and runs it."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.runner.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=1, user={"username": "test"})

            MockWorker.assert_called_once_with(
                job_id=1,
                user={"username": "test"},
                cancel_event=None,
                args=None,
            )
            mock_instance.run.assert_called_once()

    def test_entry_point_with_cancel_event(self):
        """Test entry point with cancel event."""
        cancel_event = threading.Event()
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.runner.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=1, user=None, cancel_event=cancel_event)

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["cancel_event"] is cancel_event

    def test_entry_point_accepts_args_keyword_param(self):
        """Test that the entry point accepts args= keyword-only param."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.runner.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=1, user=None, args={"some_key": "value"})

            mock_instance.run.assert_called_once()

    def test_entry_point_args_defaults_to_none(self):
        """Test that args defaults to None and entry point works without it."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.runner.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=99, user=None)

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["args"] is None

    def test_entry_point_maps_owid_charts_limit_items_to_limit_items(self):
        """Test that limit_items is mapped to limit_items in args."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.runner.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(
                job_id=1,
                user=None,
                args={"limit_items": 10},
            )

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["args"]["limit_items"] == 10

    def test_entry_point_does_not_map_when_key_absent(self):
        """Test that args are passed unchanged when limit_items is absent."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.runner.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(
                job_id=1,
                user=None,
                args={"other_key": "value"},
            )

            call_kwargs = MockWorker.call_args.kwargs
            assert "limit_items" not in call_kwargs["args"]

    def test_entry_point_does_not_modify_args_when_args_is_none(self):
        """Test that entry point works correctly when args is None."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.runner.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=1, user=None, args=None)

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["args"] is None
