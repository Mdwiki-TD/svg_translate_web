from __future__ import annotations

import pytest
from src.main_app.shared.models.owid_chart_record import OwidChartRecord


def test_owid_chart_record_initialization():
    """Test OwidChartRecord initialization with required fields."""
    rec = OwidChartRecord(
        chart_id=1,
        slug="health-expenditure",
        title="Health Expenditure",
        has_map_tab=True,
        max_time=2023,
        min_time=2000,
        default_tab="chart",
        is_published=True,
        single_year_data=False,
        len_years=24,
        has_timeline=False,
    )

    assert rec.chart_id == 1
    assert rec.slug == "health-expenditure"
    assert rec.title == "Health Expenditure"
    assert rec.has_map_tab is True
    assert rec.max_time == 2023
    assert rec.min_time == 2000
    assert rec.default_tab == "chart"
    assert rec.is_published is True
    assert rec.single_year_data is False
    assert rec.len_years == 24
    assert rec.created_at is None
    assert rec.updated_at is None
    assert rec.template_id is None
    assert rec.template_title is None
    assert rec.template_source == "https://ourworldindata.org/grapher/health-expenditure"


def test_owid_chart_record_with_all_fields():
    """Test OwidChartRecord initialization with all fields."""
    rec = OwidChartRecord(
        chart_id=1,
        slug="health-expenditure",
        title="Health Expenditure",
        has_map_tab=True,
        max_time=2023,
        min_time=2000,
        default_tab="chart",
        is_published=True,
        single_year_data=False,
        len_years=24,
        created_at="2023-01-01",
        updated_at="2023-01-02",
        template_id=42,
        template_title="Template:Health",
        template_source="https://example.com/template",
        has_timeline=True,
    )

    assert rec.chart_id == 1
    assert rec.slug == "health-expenditure"
    assert rec.title == "Health Expenditure"
    assert rec.has_map_tab is True
    assert rec.max_time == 2023
    assert rec.min_time == 2000
    assert rec.default_tab == "chart"
    assert rec.is_published is True
    assert rec.single_year_data is False
    assert rec.len_years == 24
    assert rec.created_at == "2023-01-01"
    assert rec.updated_at == "2023-01-02"
    assert rec.template_id == 42
    assert rec.template_title == "Template:Health"
    assert rec.template_source == "https://example.com/template"


def test_owid_chart_record_template_source_generation():
    """Test template source generation from slug."""
    rec = OwidChartRecord(
        chart_id=1,
        slug="health-expenditure",
        title="Health Expenditure",
        has_map_tab=True,
        max_time=2023,
        min_time=2000,
        default_tab="chart",
        is_published=True,
        single_year_data=False,
        len_years=24,
        has_timeline=False,
    )

    # Template source should be generated from slug
    assert rec.template_source == "https://ourworldindata.org/grapher/health-expenditure"


def test_owid_chart_record_no_template_source_generation():
    """Test that template source is not generated when slug is missing."""
    rec = OwidChartRecord(
        chart_id=1,
        slug="",  # Empty slug
        title="Health Expenditure",
        has_map_tab=True,
        max_time=2023,
        min_time=2000,
        default_tab="chart",
        is_published=True,
        single_year_data=False,
        len_years=24,
        has_timeline=False,
    )

    # Template source should remain None
    assert rec.template_source is None


def test_owid_chart_record_template_source_preserved():
    """Test that existing template source is not overwritten."""
    rec = OwidChartRecord(
        chart_id=1,
        slug="health-expenditure",
        title="Health Expenditure",
        has_map_tab=True,
        max_time=2023,
        min_time=2000,
        default_tab="chart",
        is_published=True,
        single_year_data=False,
        len_years=24,
        has_timeline=False,
        template_source="https://custom.source/template",
    )

    # Existing template source should be preserved
    assert rec.template_source == "https://custom.source/template"


def test_owid_chart_record_boolean_fields():
    """Test boolean fields."""
    rec = OwidChartRecord(
        chart_id=1,
        slug="health-expenditure",
        title="Health Expenditure",
        has_map_tab=False,
        max_time=2023,
        min_time=2000,
        default_tab=None,
        is_published=False,
        single_year_data=True,
        len_years=None,
        has_timeline=False,
    )

    assert rec.has_map_tab is False
    assert rec.default_tab is None
    assert rec.is_published is False
    assert rec.single_year_data is True
    assert rec.has_timeline is False
    assert rec.len_years is None


def test_owid_chart_record_to_dict():
    """Test conversion to dictionary."""
    rec = OwidChartRecord(
        chart_id=1,
        slug="health-expenditure",
        title="Health Expenditure",
        has_map_tab=True,
        max_time=2023,
        min_time=2000,
        default_tab="chart",
        is_published=True,
        single_year_data=False,
        len_years=24,
        has_timeline=False,
        created_at="2023-01-01",
        updated_at="2023-01-02",
        template_id=42,
        template_title="Template:Health",
        template_source="https://ourworldindata.org/grapher/health-expenditure",
    )

    result = rec.to_dict()

    expected = {
        "chart_id": 1,
        "slug": "health-expenditure",
        "title": "Health Expenditure",
        "has_map_tab": True,
        "max_time": 2023,
        "min_time": 2000,
        "default_tab": "chart",
        "is_published": True,
        "single_year_data": False,
        "len_years": 24,
        "has_timeline": False,
        "created_at": "2023-01-01",
        "updated_at": "2023-01-02",
        "template_id": 42,
        "template_title": "Template:Health",
        "template_source": "https://ourworldindata.org/grapher/health-expenditure",
    }

    assert result == expected


def test_owid_chart_record_to_dict_with_none_values():
    """Test conversion to dictionary with None values."""
    rec = OwidChartRecord(
        chart_id=1,
        slug="health-expenditure",
        title="Health Expenditure",
        has_map_tab=False,
        max_time=None,
        min_time=None,
        default_tab=None,
        is_published=False,
        single_year_data=True,
        len_years=None,
        has_timeline=False,
        created_at=None,
        updated_at=None,
        template_id=None,
        template_title=None,
        template_source=None,
    )

    result = rec.to_dict()

    expected = {
        "chart_id": 1,
        "slug": "health-expenditure",
        "title": "Health Expenditure",
        "has_map_tab": False,
        "max_time": None,
        "min_time": None,
        "default_tab": None,
        "is_published": False,
        "single_year_data": True,
        "len_years": None,
        "has_timeline": False,
        "created_at": None,
        "updated_at": None,
        "template_id": None,
        "template_title": None,
        "template_source": None,
    }

    assert result == expected
