"""Unit tests for update_owid_charts/worker module."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import OwidChartRecord
from src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker import (
    UpdateOwidChartsWorker,
)

_WORKER = "src.main_app.jobs_workers.admin_jobs_workers.update_owid_charts.worker"


@dataclass
class MockServices:
    check_slugs: MagicMock
    fetch_grapher_metadata: MagicMock
    owid_charts_service_class: MagicMock
    owid_charts_service: MagicMock


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch) -> MockServices:
    """Bundle of mocked worker dependencies for update_owid_charts."""
    mock_check_slugs = MagicMock()
    monkeypatch.setattr(f"{_WORKER}.check_slugs", mock_check_slugs)

    # _fetch_grapher_metadata returns (metadata, status_code)
    mock_fetch = MagicMock(return_value=(None, 200))
    monkeypatch.setattr(f"{_WORKER}._fetch_grapher_metadata", mock_fetch)

    mock_service = MagicMock()
    mock_service_class = MagicMock(return_value=mock_service)
    monkeypatch.setattr(f"{_WORKER}.OwidChartsService", mock_service_class)

    return MockServices(
        check_slugs=mock_check_slugs,
        fetch_grapher_metadata=mock_fetch,
        owid_charts_service_class=mock_service_class,
        owid_charts_service=mock_service,
    )


class TestUpdateOwidChartsWorkerInitialization:
    """Tests for UpdateOwidChartsWorker initialization."""

    def test_worker_initialization(self):
        """Test worker initializes correctly with default args."""
        worker = UpdateOwidChartsWorker(job_id=1, user={"username": "test"}, cancel_event=None)

        assert worker.job_id == 1
        assert worker.user == {"username": "test"}
        assert worker.get_job_type() == "update_owid_charts"
        assert worker.limit_items == 0

    def test_worker_initialization_with_limit_items(self):
        """Test worker reads limit_items from args."""
        worker = UpdateOwidChartsWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": 5},
        )

        assert worker.limit_items == 5

    def test_worker_initialization_with_none_args(self):
        """Test worker defaults limit_items to 0 when args is None."""
        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None, args=None)

        assert worker.limit_items == 0

    def test_worker_initialization_limit_items_none_when_key_missing(self):
        """Test worker sets limit_items to None when args has no limit_items key."""
        worker = UpdateOwidChartsWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"other_key": "value"},
        )

        assert worker.limit_items == 0

    def test_get_job_type(self):
        """Test get_job_type returns correct value."""
        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        assert worker.get_job_type() == "update_owid_charts"

    def test_initial_result_structure(self):
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

    def test_apply_limits_with_limit_set(self):
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

    def test_apply_limits_with_zero_limit(self):
        """Test _apply_limits with zero limit returns all charts."""
        charts = [
            MagicMock(chart_id=1, slug="chart-1"),
            MagicMock(chart_id=2, slug="chart-2"),
        ]

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker._apply_limits(charts)

        assert len(result) == 2

    def test_apply_limits_with_limit_greater_than_charts(self):
        """Test _apply_limits when limit is greater than number of charts."""
        charts = [
            MagicMock(chart_id=1, slug="chart-1"),
        ]

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker._apply_limits(charts)

        assert len(result) == 1

    def test_apply_limits_with_non_integer_limit(self):
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


class TestProcessChart:
    """Tests for _process_chart method."""

    def test_process_chart_404(self, mock_services: MockServices):
        """When fetch_grapher_metadata returns 404 -> status 'skipped' with 'not found' reason."""
        mock_services.fetch_grapher_metadata.return_value = (None, 404)

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
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
        assert worker.result.failed_charts[0]["error"] == "Chart not found"
        assert worker.result.failed_charts[0]["slug"] == "test-chart"
        mock_services.owid_charts_service.update_chart_data_with_retry.assert_called_once_with(
            1, {"status_404": 404}
        )

    def test_process_chart_metadata_none(self, mock_services: MockServices):
        """When fetch_grapher_metadata returns None -> status 'failed'."""
        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
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

    def test_process_chart_nothing_to_update(self, mock_services: MockServices):
        """When metadata has no timespan AND no owidVariableId -> skipped."""
        metadata = {"columns": {"col1": {"some_key": "some_value"}}}
        mock_services.fetch_grapher_metadata.return_value = (metadata, 200)

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
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

    def test_process_chart_owid_variable_id_update_only(self, mock_services: MockServices):
        """When only owid_variable_id changes -> calls update_chart_data_with_retry."""
        metadata = {"columns": {"col1": {"owidVariableId": 123}}}
        mock_services.fetch_grapher_metadata.return_value = (metadata, 200)

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
            chart_id=1,
            slug="test-chart",
            min_time=None,
            max_time=None,
            len_years=None,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is True
        mock_services.owid_charts_service.update_chart_data_with_retry.assert_called_once_with(
            1, {"owid_variable_id": 123}
        )
        assert len(worker.result.updated_charts) == 1

    def test_process_chart_parse_timespan_fails(self, mock_services: MockServices):
        """When timespan exists but cannot be parsed -> failed."""
        metadata = {"columns": {"col1": {"timespan": "invalid"}}}
        mock_services.fetch_grapher_metadata.return_value = (metadata, 200)

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
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

    def test_process_chart_full_update(self, mock_services: MockServices):
        """When both timespan parsed and owid_variable_id changed -> full update."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020", "owidVariableId": 123}}}
        mock_services.fetch_grapher_metadata.return_value = (metadata, 200)

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
            chart_id=1,
            slug="test-chart",
            min_time=1990,
            max_time=1995,
            len_years=6,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is True
        mock_services.owid_charts_service.update_chart_data_with_retry.assert_called_once_with(
            1,
            {"min_time": 2000, "max_time": 2020, "len_years": 21, "owid_variable_id": 123},
        )

    def test_process_chart_no_change_timespan(self, mock_services: MockServices):
        """When timespan values match existing -> skipped."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020"}}}
        mock_services.fetch_grapher_metadata.return_value = (metadata, 200)

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
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

    def test_process_chart_db_update_exception(self, mock_services: MockServices):
        """When update_chart_data_with_retry raises -> status failed."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020"}}}
        mock_services.fetch_grapher_metadata.return_value = (metadata, 200)
        mock_services.owid_charts_service.update_chart_data_with_retry.side_effect = Exception("DB error")

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
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

    def test_process_chart_timespan_no_owid_variable_id(self, mock_services: MockServices):
        """When owid_variable_id is None and chart has none -> no variable update."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020"}}}
        mock_services.fetch_grapher_metadata.return_value = (metadata, 200)

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
            chart_id=1,
            slug="test-chart",
            min_time=1990,
            max_time=1995,
            len_years=6,
            owid_variable_id=None,
        )

        result = worker._process_chart(chart)

        assert result is True
        mock_services.owid_charts_service.update_chart_data_with_retry.assert_called_once_with(
            1,
            {"min_time": 2000, "max_time": 2020, "len_years": 21},
        )

    def test_process_chart_owid_variable_id_same(self, mock_services: MockServices):
        """When owid_variable_id matches existing -> no update."""
        metadata = {"columns": {"col1": {"timespan": "2000-2020", "owidVariableId": 42}}}
        mock_services.fetch_grapher_metadata.return_value = (metadata, 200)

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        chart = OwidChartRecord(
            chart_id=1,
            slug="test-chart",
            min_time=2000,
            max_time=2020,
            len_years=21,
            owid_variable_id=42,
        )

        result = worker._process_chart(chart)

        assert result is False
        mock_services.owid_charts_service.update_chart_data_with_retry.assert_not_called()
        assert len(worker.result.skipped_charts) == 1
        assert worker.result.skipped_charts[0]["skip_reason"] == "nothing to update"


class TestProcess:
    """Tests for process method."""

    def test_process_empty_charts(self, mock_services: MockServices):
        """When no charts loaded -> completed with total=0."""
        mock_services.owid_charts_service.list_charts.return_value = []

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result.status == "failed"
        assert result.summary.total == 0

    def test_process_single_chart(self, mock_services: MockServices, monkeypatch: pytest.MonkeyPatch):
        """When one chart processes successfully -> completed."""
        chart = OwidChartRecord(
            chart_id=1,
            slug="test-chart",
            min_time=2000,
            max_time=2020,
            len_years=21,
            owid_variable_id=None,
        )
        mock_services.owid_charts_service.list_charts.return_value = [chart]

        mock_process_chart = MagicMock(return_value=True)
        monkeypatch.setattr(
            f"{_WORKER}.UpdateOwidChartsWorker._process_chart",
            mock_process_chart,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process_all()

        mock_process_chart.assert_called_once_with(chart)
        assert result.status == "completed"
        assert result.summary.total == 1

    def test_process_cancelled_during_loop(self, mock_services: MockServices, monkeypatch: pytest.MonkeyPatch):
        """When is_cancelled() returns True -> stops early."""
        mock_services.owid_charts_service.list_charts.return_value = [
            MagicMock(chart_id=1, slug="chart-1"),
            MagicMock(chart_id=2, slug="chart-2"),
        ]

        mock_is_cancelled = MagicMock(return_value=True)
        monkeypatch.setattr(
            f"{_WORKER}.UpdateOwidChartsWorker.is_cancelled",
            mock_is_cancelled,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process_all()

        assert result.summary.total == 2
        assert result.summary.processed == 0

    def test_process_cancelled_by_periodic_check(self, mock_services: MockServices, monkeypatch: pytest.MonkeyPatch):
        """When check_cancel_db_periodic() returns True -> stops, saves progress."""
        chart1 = MagicMock(chart_id=1, slug="chart-1")
        chart2 = MagicMock(chart_id=2, slug="chart-2")
        mock_services.owid_charts_service.list_charts.return_value = [chart1, chart2]

        mock_process_chart = MagicMock(return_value=True)
        monkeypatch.setattr(
            f"{_WORKER}.UpdateOwidChartsWorker._process_chart",
            mock_process_chart,
        )
        mock_cancel_periodic = MagicMock(return_value=True)
        monkeypatch.setattr(
            f"{_WORKER}.UpdateOwidChartsWorker.check_cancel_db_periodic",
            mock_cancel_periodic,
        )

        worker = UpdateOwidChartsWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process_all()

        mock_process_chart.assert_called_once()
        assert result.summary.total == 2
