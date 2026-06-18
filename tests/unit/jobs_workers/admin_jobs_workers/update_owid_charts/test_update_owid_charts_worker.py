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

        assert worker.limit_items == 0

    def test_get_job_type(self, mock_jobs_service):
        """Test get_job_type returns correct value."""
        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        assert worker.get_job_type() == "update_owid_charts"

    def test_initial_result_structure(self, mock_jobs_service):
        """Test initial result matches expected structure."""
        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.result

        assert result.status == "pending"
        assert result.started_at is not None
        assert result.completed_at is None
        assert result.cancelled_at is None
        assert result.summary.total == 0
        assert result.summary.processed == 0
        assert result.summary.updated == 0
        assert result.summary.skipped == 0
        assert result.summary.failed == 0
        assert result.pages_processed == []


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
        """Test that limit_items is mapped to limit_items in args."""
        with patch(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker"
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

    def test_entry_point_does_not_map_when_key_absent(self, mock_jobs_service):
        """Test that args are passed unchanged when limit_items is absent."""
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


class TestProcessChart:
    """Tests for _process_chart method."""

    def test_process_chart_metadata_none(self, mock_jobs_service, monkeypatch):
        """When fetch_grapher_metadata returns None -> status 'failed'."""
        mock_fetch = MagicMock(return_value=None)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=2000,
            max_time=2020,
            len_years=21,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is False
        assert len(worker.result.failed_charts) == 1
        assert worker.result.failed_charts[0]["status"] == "failed"
        assert worker.result.failed_charts[0]["error"] == "Could not fetch metadata JSON"

    def test_process_chart_nothing_to_update(self, mock_jobs_service, monkeypatch):
        """When metadata has no timespan AND no owidVariableId -> skipped."""
        metadata = {"columns": {"col1": {"some_key": "some_value"}}}
        mock_fetch = MagicMock(return_value=metadata)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.check_slugs",
            MagicMock(),
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=None,
            max_time=None,
            len_years=None,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is False
        assert len(worker.result.skipped_charts) == 1
        assert worker.result.skipped_charts[0]["status"] == "skipped"
        assert worker.result.skipped_charts[0]["skip_reason"] == "nothing to update"

    def test_process_chart_owid_variable_id_update_only(self, mock_jobs_service, monkeypatch):
        """When only owid_variable_id changes -> calls update_chart_data."""
        metadata = {"columns": {"col1": {"owidVariableId": 123}}}
        mock_fetch = MagicMock(return_value=metadata)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.check_slugs",
            MagicMock(),
        )

        mock_service = MagicMock()
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=None,
            max_time=None,
            len_years=None,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is True
        mock_service.update_chart_data.assert_called_once_with(1, {"owid_variable_id": 123})
        assert len(worker.result.updated_charts) == 1

    def test_process_chart_parse_timespan_fails(self, mock_jobs_service, monkeypatch):
        """When timespan exists but cannot be parsed -> failed."""
        metadata = {"columns": {"col1": {"timespan": "invalid"}}}
        mock_fetch = MagicMock(return_value=metadata)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.check_slugs",
            MagicMock(),
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=None,
            max_time=None,
            len_years=None,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is False
        assert len(worker.result.failed_charts) == 1
        assert "Could not parse timespan" in worker.result.failed_charts[0]["error"]

    def test_process_chart_full_update(self, mock_jobs_service, monkeypatch):
        """When both timespan parsed and owid_variable_id changed -> full update."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020", "owidVariableId": 123}}}
        mock_fetch = MagicMock(return_value=metadata)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.check_slugs",
            MagicMock(),
        )

        mock_service = MagicMock()
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=1990,
            max_time=1995,
            len_years=6,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is True
        mock_service.update_chart_data.assert_called_once_with(
            1,
            {"min_time": 2000, "max_time": 2020, "len_years": 21, "owid_variable_id": 123},
        )

    def test_process_chart_no_change_timespan(self, mock_jobs_service, monkeypatch):
        """When timespan values match existing -> skipped."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020"}}}
        mock_fetch = MagicMock(return_value=metadata)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.check_slugs",
            MagicMock(),
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=2000,
            max_time=2020,
            len_years=21,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is False
        assert len(worker.result.skipped_charts) == 1
        assert worker.result.skipped_charts[0]["skip_reason"] == "nothing to update"

    def test_process_chart_db_update_exception(self, mock_jobs_service, monkeypatch):
        """When update_chart_data raises -> status failed."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020"}}}
        mock_fetch = MagicMock(return_value=metadata)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.check_slugs",
            MagicMock(),
        )

        mock_service = MagicMock()
        mock_service.update_chart_data.side_effect = Exception("DB error")
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=1990,
            max_time=1995,
            len_years=6,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is False
        assert len(worker.result.failed_charts) == 1
        assert worker.result.failed_charts[0]["status"] == "failed"
        assert worker.result.failed_charts[0]["error"] == "DB error"

    def test_process_chart_timespan_no_owid_variable_id(self, mock_jobs_service, monkeypatch):
        """When owid_variable_id is None and chart has none -> no variable update."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020"}}}
        mock_fetch = MagicMock(return_value=metadata)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.check_slugs",
            MagicMock(),
        )

        mock_service = MagicMock()
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=1990,
            max_time=1995,
            len_years=6,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is True
        mock_service.update_chart_data.assert_called_once_with(
            1,
            {"min_time": 2000, "max_time": 2020, "len_years": 21},
        )

    def test_process_chart_owid_variable_id_same(self, mock_jobs_service, monkeypatch):
        """When owid_variable_id matches existing -> no update."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020", "owidVariableId": 42}}}
        mock_fetch = MagicMock(return_value=metadata)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.fetch_grapher_metadata",
            mock_fetch,
        )
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.check_slugs",
            MagicMock(),
        )

        mock_service = MagicMock()
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=2000,
            max_time=2020,
            len_years=21,
            owid_variable_id=42,
        )

        result = worker._process_chart(chart)

        assert result is False
        mock_service.update_chart_data.assert_not_called()
        assert len(worker.result.skipped_charts) == 1
        assert worker.result.skipped_charts[0]["skip_reason"] == "nothing to update"


class TestProcess:
    """Tests for process method."""

    def test_process_empty_charts(self, mock_jobs_service, monkeypatch):
        """When no charts loaded -> completed with total=0."""
        mock_service = MagicMock()
        mock_service.list_charts.return_value = []
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result.status == "completed"
        assert result.summary.total == 0

    def test_process_single_chart(self, mock_jobs_service, monkeypatch):
        """When one chart processes successfully -> completed."""
        mock_service = MagicMock()
        chart = MagicMock(
            chart_id=1,
            slug="test-chart",
            min_time=2000,
            max_time=2020,
            len_years=21,
            owid_variable_id=None,
        )
        mock_service.list_charts.return_value = [chart]
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        mock_process_chart = MagicMock(return_value=True)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker._process_chart",
            mock_process_chart,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        mock_process_chart.assert_called_once_with(chart)
        assert result.status == "completed"
        assert result.summary.total == 1

    def test_process_cancelled_during_loop(self, mock_jobs_service, monkeypatch):
        """When is_cancelled() returns True -> stops early."""
        mock_service = MagicMock()
        mock_service.list_charts.return_value = [
            MagicMock(chart_id=1, slug="chart-1"),
            MagicMock(chart_id=2, slug="chart-2"),
        ]
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        mock_is_cancelled = MagicMock(return_value=True)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker.is_cancelled",
            mock_is_cancelled,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result.summary.total == 2
        assert result.summary.processed == 0

    def test_process_cancelled_by_periodic_check(self, mock_jobs_service, monkeypatch):
        """When check_cancel_db_periodic() returns True -> stops, saves progress."""
        mock_service = MagicMock()
        chart1 = MagicMock(chart_id=1, slug="chart-1")
        chart2 = MagicMock(chart_id=2, slug="chart-2")
        mock_service.list_charts.return_value = [chart1, chart2]
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.owid_charts_service",
            mock_service,
        )

        mock_process_chart = MagicMock(return_value=True)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker._process_chart",
            mock_process_chart,
        )
        mock_cancel_periodic = MagicMock(return_value=True)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker.UpdateOwidChartsWorker.check_cancel_db_periodic",
            mock_cancel_periodic,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        mock_process_chart.assert_called_once()
        assert result.summary.total == 2
