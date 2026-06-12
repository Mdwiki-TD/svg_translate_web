"""Unit tests for update_owid_charts/worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker import (
    UpdateOwidChartsWorker,
    update_owid_charts_worker_entry,
)


class TestUpdateOwidChartsWorkerInitialization:
    """Tests for UpdateOwidChartsWorker initialization."""

    def test_worker_initialization(self, mock_jobs_service):
        """Test worker initializes correctly with default args."""
        worker = UpdateOwidChartsWorker(job_id=1, user={"username": "test"}, cancel_event=None)

        assert worker.job_id == 1
        assert worker.user == {"username": "test"}
        assert worker.get_job_type() == "update_owid_charts"
        assert worker.limit_items == 0

    def test_worker_initialization_with_limit_items(self, mock_jobs_service):
        """Test worker reads limit_items from args."""
        worker = UpdateOwidChartsWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": 5},
        )

        assert worker.limit_items == 5

    def test_worker_initialization_with_none_args(self, mock_jobs_service):
        """Test worker defaults limit_items to 0 when args is None."""
        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None, args=None)

        assert worker.limit_items == 0

    def test_worker_initialization_limit_items_none_when_key_missing(self, mock_jobs_service):
        """Test worker sets limit_items to None when args has no limit_items key."""
        worker = UpdateOwidChartsWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"other_key": "value"},
        )

        assert worker.limit_items is None

    def test_get_job_type(self, mock_jobs_service):
        """Test get_job_type returns correct value."""
        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        assert worker.get_job_type() == "update_owid_charts"

    def test_get_initial_result(self, mock_jobs_service):
        """Test get_initial_result returns proper structure."""
        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.get_initial_result()

        assert result["status"] == "pending"
        assert "started_at" in result
        assert result["completed_at"] is None
        assert result["cancelled_at"] is None
        assert result["summary"]["total"] == 0
        assert result["summary"]["processed"] == 0
        assert result["summary"]["updated"] == 0
        assert result["summary"]["skipped"] == 0
        assert result["summary"]["failed"] == 0
        assert result["charts_processed"] == []


class TestUpdateOwidChartsWorkerApplyLimits:
    """Tests for _apply_limits method."""

    def test_apply_limits_with_limit_set(self, mock_jobs_service):
        """Test _apply_limits respects the limit_items setting."""
        charts = [
            MagicMock(chart_id=1, slug="chart-1"),
            MagicMock(chart_id=2, slug="chart-2"),
            MagicMock(chart_id=3, slug="chart-3"),
        ]

        worker = UpdateOwidChartsWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": 2},
        )
        result = worker._apply_limits(charts)

        assert len(result) == 2

    def test_apply_limits_with_zero_limit(self, mock_jobs_service):
        """Test _apply_limits with zero limit returns all charts."""
        charts = [
            MagicMock(chart_id=1, slug="chart-1"),
            MagicMock(chart_id=2, slug="chart-2"),
        ]

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker._apply_limits(charts)

        assert len(result) == 2

    def test_apply_limits_with_limit_greater_than_charts(self, mock_jobs_service):
        """Test _apply_limits when limit is greater than number of charts."""
        charts = [
            MagicMock(chart_id=1, slug="chart-1"),
        ]

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker._apply_limits(charts)

        assert len(result) == 1

    def test_apply_limits_with_non_integer_limit(self, mock_jobs_service):
        """Test _apply_limits treats non-integer limit as 0."""
        charts = [
            MagicMock(chart_id=1, slug="chart-1"),
            MagicMock(chart_id=2, slug="chart-2"),
        ]

        worker = UpdateOwidChartsWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": "not_an_int"},
        )
        result = worker._apply_limits(charts)

        assert len(result) == 2


class TestUpdateOwidChartsWorkerEntry:
    """Tests for update_owid_charts_worker_entry entry point."""

    def test_entry_point_creates_worker_and_runs(self, mock_jobs_service):
        """Test that entry point creates worker and runs it."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
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

    def test_entry_point_with_cancel_event(self, mock_jobs_service):
        """Test entry point with cancel event."""
        cancel_event = threading.Event()
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=1, user=None, cancel_event=cancel_event)

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["cancel_event"] is cancel_event

    def test_entry_point_accepts_args_keyword_param(self, mock_jobs_service):
        """Test that the entry point accepts args= keyword-only param."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=1, user=None, args={"some_key": "value"})

            mock_instance.run.assert_called_once()

    def test_entry_point_args_defaults_to_none(self, mock_jobs_service):
        """Test that args defaults to None and entry point works without it."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=99, user=None)

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["args"] is None

    def test_entry_point_maps_owid_charts_limit_items_to_limit_items(self, mock_jobs_service):
        """Test that owid_charts_limit_items is mapped to limit_items in args."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(
                job_id=1,
                user=None,
                args={"owid_charts_limit_items": 10},
            )

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["args"]["limit_items"] == 10

    def test_entry_point_does_not_map_when_key_absent(self, mock_jobs_service):
        """Test that args are passed unchanged when owid_charts_limit_items is absent."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
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

    def test_entry_point_does_not_map_when_value_falsy(self, mock_jobs_service):
        """Test that mapping is skipped when owid_charts_limit_items value is falsy."""
        for falsy_value in [0, None, "", False]:
            with patch(
                "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
            ) as MockWorker:
                mock_instance = MagicMock()
                MockWorker.return_value = mock_instance

                update_owid_charts_worker_entry(
                    job_id=1,
                    user=None,
                    args={"owid_charts_limit_items": falsy_value},
                )

                call_kwargs = MockWorker.call_args.kwargs
                assert "limit_items" not in call_kwargs["args"], f"Should not map for falsy value: {falsy_value!r}"

    def test_entry_point_does_not_modify_args_when_args_is_none(self, mock_jobs_service):
        """Test that entry point works correctly when args is None."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            update_owid_charts_worker_entry(job_id=1, user=None, args=None)

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["args"] is None
