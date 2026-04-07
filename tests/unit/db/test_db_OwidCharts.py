"""Tests for src.main_app.db.db_OwidCharts."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.db.db_OwidCharts import OwidChartsDB
from src.main_app.shared.models import OwidChartRecord


@pytest.fixture
def mock_db():
    """Create a mock Database instance."""
    return MagicMock()


@pytest.fixture
def mock_db_config():
    """Create a mock DbConfig instance."""
    config = MagicMock()
    return config


@pytest.fixture
def sample_row():
    """Create a sample database row dict."""
    return {
        "chart_id": 1,
        "slug": "test-chart",
        "title": "Test Chart",
        "has_map_tab": 1,
        "max_time": 2024,
        "min_time": 2000,
        "default_tab": "chart",
        "is_published": 1,
        "single_year_data": 0,
        "len_years": 25,
        "has_timeline": 1,
        "created_at": "2024-01-01 00:00:00",
        "updated_at": "2024-01-02 00:00:00",
        "template_id": 10,
        "template_title": "Test Template",
        "template_source": None,
    }


class TestOwidChartRecord:
    """Tests for OwidChartRecord dataclass."""

    def test_basic_creation(self):
        """Test creating a record with required fields."""
        record = OwidChartRecord(
            chart_id=1,
            slug="test-chart",
            title="Test Chart",
            has_map_tab=True,
            max_time=2024,
            min_time=2000,
            default_tab=None,
            is_published=True,
            single_year_data=False,
            len_years=None,
            has_timeline=False,
        )
        assert record.chart_id == 1
        assert record.slug == "test-chart"
        assert record.title == "Test Chart"
        assert record.has_map_tab is True
        assert record.is_published is True

    def test_template_source_auto_generated(self):
        """Test that template_source is auto-generated from slug."""
        record = OwidChartRecord(
            chart_id=1,
            slug="my-chart",
            title="My Chart",
            has_map_tab=False,
            max_time=None,
            min_time=None,
            default_tab=None,
            is_published=False,
            single_year_data=False,
            len_years=None,
            has_timeline=False,
        )
        assert record.template_source == "https://ourworldindata.org/grapher/my-chart"

    def test_optional_fields_default_none(self):
        """Test that optional fields default to None."""
        record = OwidChartRecord(
            chart_id=1,
            slug="test",
            title="Test",
            has_map_tab=False,
            max_time=None,
            min_time=None,
            default_tab=None,
            is_published=False,
            single_year_data=False,
            len_years=None,
            has_timeline=False,
        )
        assert record.created_at is None
        assert record.updated_at is None
        assert record.template_id is None
        assert record.template_title is None


class TestOwidChartsDB:
    """Tests for OwidChartsDB class."""

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_init_creates_table(self, mock_database_cls, mock_db_config):
        """Test that initialization ensures table exists."""
        mock_db_instance = MagicMock()
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)

        assert mock_db_instance.execute_query_safe.call_count == 2

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_fetch_by_id_success(self, mock_database_cls, mock_db_config, sample_row):
        """Test fetching a chart by ID."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = [sample_row]
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        result = db.fetch_by_id(1)

        assert isinstance(result, OwidChartRecord)
        assert result.chart_id == 1
        assert result.slug == "test-chart"

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_fetch_by_id_not_found(self, mock_database_cls, mock_db_config):
        """Test fetching a non-existent chart raises LookupError."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = []
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)

        with pytest.raises(LookupError, match="Chart id 999 was not found"):
            db.fetch_by_id(999)

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_fetch_by_slug_success(self, mock_database_cls, mock_db_config, sample_row):
        """Test fetching a chart by slug."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = [sample_row]
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        result = db.fetch_by_slug("test-chart")

        assert result.slug == "test-chart"
        assert result.title == "Test Chart"

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_fetch_by_slug_not_found(self, mock_database_cls, mock_db_config):
        """Test fetching by non-existent slug raises LookupError."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = []
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)

        with pytest.raises(LookupError, match="Chart slug 'missing' was not found"):
            db.fetch_by_slug("missing")

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_list_returns_all_charts(self, mock_database_cls, mock_db_config, sample_row):
        """Test listing all charts."""
        rows = [sample_row, {**sample_row, "chart_id": 2, "slug": "chart-2"}]
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = rows
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        results = db.list()

        assert len(results) == 2
        assert all(isinstance(r, OwidChartRecord) for r in results)

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_list_published_filters_published(self, mock_database_cls, mock_db_config, sample_row):
        """Test listing only published charts."""
        published_row = {**sample_row, "is_published": 1}
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = [published_row]
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        results = db.list_published()

        assert len(results) == 1
        assert results[0].is_published is True

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_add_success(self, mock_database_cls, mock_db_config, sample_row):
        """Test adding a new chart."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = [sample_row]
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        result = db.add(slug="new-chart", title="New Chart")

        mock_db_instance.execute_query.assert_called_once()
        assert isinstance(result, OwidChartRecord)

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_add_missing_slug_raises_value_error(self, mock_database_cls, mock_db_config):
        """Test adding a chart with empty slug raises ValueError."""
        mock_db_instance = MagicMock()
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)

        with pytest.raises(ValueError, match="Slug is required"):
            db.add(slug="", title="New Chart")

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_add_missing_title_raises_value_error(self, mock_database_cls, mock_db_config):
        """Test adding a chart with empty title raises ValueError."""
        mock_db_instance = MagicMock()
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)

        with pytest.raises(ValueError, match="Title is required"):
            db.add(slug="new-chart", title="")

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_add_duplicate_slug_raises_value_error(self, mock_database_cls, mock_db_config):
        """Test adding a chart with duplicate slug raises ValueError."""
        import pymysql

        mock_db_instance = MagicMock()
        mock_db_instance.execute_query.side_effect = pymysql.err.IntegrityError()
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)

        with pytest.raises(ValueError, match="Chart with slug 'existing' already exists"):
            db.add(slug="existing", title="Existing Chart")

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_update_success(self, mock_database_cls, mock_db_config, sample_row):
        """Test updating an existing chart."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = [sample_row]
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        result = db.update(chart_id=1, slug="updated-slug", title="Updated Title")

        mock_db_instance.execute_query_safe.assert_called()
        assert result.slug == "test-chart"  # Returns fetched record

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_update_nonexistent_raises_lookup_error(self, mock_database_cls, mock_db_config):
        """Test updating a non-existent chart raises LookupError."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = []
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)

        with pytest.raises(LookupError):
            db.update(chart_id=999, slug="new", title="New")

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_delete_success(self, mock_database_cls, mock_db_config, sample_row):
        """Test deleting a chart."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = [sample_row]
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        result = db.delete(chart_id=1)

        assert isinstance(result, OwidChartRecord)
        mock_db_instance.execute_query_safe.assert_called()

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_delete_nonexistent_raises_lookup_error(self, mock_database_cls, mock_db_config):
        """Test deleting a non-existent chart raises LookupError."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = []
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)

        with pytest.raises(LookupError):
            db.delete(chart_id=999)

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_update_chart_data_partial_update(self, mock_database_cls, mock_db_config, sample_row):
        """Test updating only specific chart fields."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = [sample_row]
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        result = db.update_chart_data(chart_id=1, chart_data={"title": "New Title"})

        mock_db_instance.execute_query_safe.assert_called()
        assert isinstance(result, OwidChartRecord)

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_update_chart_data_boolean_fields(self, mock_database_cls, mock_db_config, sample_row):
        """Test that boolean fields are converted to 0/1."""
        mock_db_instance = MagicMock()
        mock_db_instance.fetch_query_safe.return_value = [sample_row]
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        db.update_chart_data(chart_id=1, chart_data={"is_published": True, "has_map_tab": False})

        call_args = mock_db_instance.execute_query_safe.call_args
        query = call_args[0][0]
        values = call_args[0][1]
        assert "is_published" in query
        assert 1 in values
        assert 0 in values

    @patch("src.main_app.db.db_OwidCharts.Database")
    def test_row_to_record_converts_booleans(self, mock_database_cls, mock_db_config):
        """Test that _row_to_record converts integer flags to booleans."""
        mock_db_instance = MagicMock()
        mock_database_cls.return_value = mock_db_instance

        db = OwidChartsDB(mock_db_config)
        row = {
            "chart_id": 1,
            "slug": "test",
            "title": "Test",
            "has_map_tab": 0,
            "max_time": None,
            "min_time": None,
            "default_tab": None,
            "is_published": 1,
            "single_year_data": 0,
            "len_years": None,
            "has_timeline": 1,
        }

        record = db._row_to_record(row)

        assert record.has_map_tab is False
        assert record.is_published is True
        assert record.has_timeline is True
