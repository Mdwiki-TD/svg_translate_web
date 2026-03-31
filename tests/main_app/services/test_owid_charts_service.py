"""Tests for src.main_app.owid_charts_service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.services.owid_charts_service import (
    add_chart,
    delete_chart,
    get_chart,
    get_chart_by_slug,
    get_owid_charts_db,
    list_charts,
    list_published_charts,
    update_chart,
    update_chart_data,
)


@pytest.fixture
def sample_record():
    """Create a sample OwidChartRecord."""
    from src.main_app.db.db_OwidCharts import OwidChartRecord

    return OwidChartRecord(
        chart_id=1,
        slug="test-chart",
        title="Test Chart",
        has_map_tab=True,
        max_time=2024,
        min_time=2000,
        default_tab="chart",
        is_published=True,
        single_year_data=False,
        len_years=25,
        has_timeline=True,
    )


@pytest.fixture
def mock_db_instance():
    """Create a mock OwidChartsDB instance."""
    return MagicMock()


class TestGetOwidChartsDb:
    """Tests for get_owid_charts_db function."""

    def test_raises_runtime_error_without_db_config(self):
        """Test that RuntimeError is raised when no DB config exists."""
        with patch("src.main_app.owid_charts_service.has_db_config", return_value=False):
            with patch("src.main_app.owid_charts_service._OWID_CHARTS_STORE", None):
                with pytest.raises(RuntimeError, match="requires database configuration"):
                    get_owid_charts_db()

    def test_raises_runtime_error_on_init_failure(self):
        """Test that RuntimeError is raised when DB init fails."""
        with patch("src.main_app.owid_charts_service.has_db_config", return_value=True):
            with patch("src.main_app.owid_charts_service._OWID_CHARTS_STORE", None):
                with patch("src.main_app.owid_charts_service.settings") as mock_settings:
                    mock_settings.database_data = MagicMock()
                    with patch(
                        "src.main_app.owid_charts_service.OwidChartsDB",
                        side_effect=Exception("DB error"),
                    ):
                        with pytest.raises(RuntimeError, match="Unable to initialize"):
                            get_owid_charts_db()

    def test_returns_initialized_instance(self):
        """Test that initialized instance is returned."""
        mock_store = MagicMock()
        with patch("src.main_app.owid_charts_service.has_db_config", return_value=True):
            with patch("src.main_app.owid_charts_service._OWID_CHARTS_STORE", None):
                with patch("src.main_app.owid_charts_service.settings") as mock_settings:
                    mock_settings.database_data = MagicMock()
                    with patch(
                        "src.main_app.owid_charts_service.OwidChartsDB",
                        return_value=mock_store,
                    ):
                        result = get_owid_charts_db()
                        assert result == mock_store


class TestListCharts:
    """Tests for list_charts function."""

    def test_returns_all_charts(self, mock_db_instance, sample_record):
        """Test that all charts are returned."""
        mock_db_instance.list.return_value = [sample_record]

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            result = list_charts()

            assert len(result) == 1
            assert result[0] == sample_record
            mock_db_instance.list.assert_called_once()


class TestListPublishedCharts:
    """Tests for list_published_charts function."""

    def test_returns_published_charts(self, mock_db_instance, sample_record):
        """Test that only published charts are returned."""
        mock_db_instance.list_published.return_value = [sample_record]

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            result = list_published_charts()

            assert len(result) == 1
            mock_db_instance.list_published.assert_called_once()


class TestGetChart:
    """Tests for get_chart function."""

    def test_returns_chart_by_id(self, mock_db_instance, sample_record):
        """Test fetching a chart by ID."""
        mock_db_instance.fetch_by_id.return_value = sample_record

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            result = get_chart(1)

            assert result == sample_record
            mock_db_instance.fetch_by_id.assert_called_once_with(1)

    def test_raises_lookup_error_for_missing(self, mock_db_instance):
        """Test that LookupError is raised for missing chart."""
        mock_db_instance.fetch_by_id.side_effect = LookupError("Not found")

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            with pytest.raises(LookupError):
                get_chart(999)


class TestGetChartBySlug:
    """Tests for get_chart_by_slug function."""

    def test_returns_chart_by_slug(self, mock_db_instance, sample_record):
        """Test fetching a chart by slug."""
        mock_db_instance.fetch_by_slug.return_value = sample_record

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            result = get_chart_by_slug("test-chart")

            assert result == sample_record
            mock_db_instance.fetch_by_slug.assert_called_once_with("test-chart")


class TestAddChart:
    """Tests for add_chart function."""

    def test_adds_chart_with_defaults(self, mock_db_instance, sample_record):
        """Test adding a chart with default values."""
        mock_db_instance.add.return_value = sample_record

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            result = add_chart(slug="new-chart", title="New Chart")

            assert result == sample_record
            mock_db_instance.add.assert_called_once_with(
                slug="new-chart",
                title="New Chart",
                has_map_tab=False,
                max_time=None,
                min_time=None,
                default_tab=None,
                is_published=False,
                single_year_data=False,
                len_years=None,
                has_timeline=False,
            )

    def test_adds_chart_with_options(self, mock_db_instance, sample_record):
        """Test adding a chart with custom options."""
        mock_db_instance.add.return_value = sample_record

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            add_chart(
                slug="new-chart",
                title="New Chart",
                has_map_tab=True,
                is_published=True,
                max_time=2024,
            )

            call_kwargs = mock_db_instance.add.call_args[1]
            assert call_kwargs["has_map_tab"] is True
            assert call_kwargs["is_published"] is True
            assert call_kwargs["max_time"] == 2024


class TestUpdateChart:
    """Tests for update_chart function."""

    def test_updates_chart(self, mock_db_instance, sample_record):
        """Test updating an existing chart."""
        mock_db_instance.update.return_value = sample_record

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            result = update_chart(chart_id=1, slug="updated", title="Updated")

            assert result == sample_record
            mock_db_instance.update.assert_called_once()
            call_kwargs = mock_db_instance.update.call_args[1]
            assert call_kwargs["chart_id"] == 1
            assert call_kwargs["slug"] == "updated"


class TestUpdateChartData:
    """Tests for update_chart_data function."""

    def test_updates_chart_data(self, mock_db_instance, sample_record):
        """Test updating chart data with a dict."""
        mock_db_instance.update_chart_data.return_value = sample_record

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            result = update_chart_data(chart_id=1, chart_data={"title": "New Title"})

            assert result == sample_record
            mock_db_instance.update_chart_data.assert_called_once_with(
                1,
                {"title": "New Title"},
            )


class TestDeleteChart:
    """Tests for delete_chart function."""

    def test_deletes_chart(self, mock_db_instance, sample_record):
        """Test deleting a chart."""
        mock_db_instance.delete.return_value = sample_record

        with patch("src.main_app.owid_charts_service.get_owid_charts_db", return_value=mock_db_instance):
            result = delete_chart(1)

            assert result == sample_record
            mock_db_instance.delete.assert_called_once_with(1)
