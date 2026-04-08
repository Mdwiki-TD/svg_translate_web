from __future__ import annotations

import pytest

from src.main_app.shared.models.template_need_update_record import TemplateNeedUpdateRecord


def test_template_need_update_record_initialization():
    """Test TemplateNeedUpdateRecord initialization with required fields."""
    rec = TemplateNeedUpdateRecord(id=1)

    assert rec.id == 1
    assert rec.template_title is None
    assert rec.slug is None
    assert rec.chart_year is None
    assert rec.template_year is None
    assert rec.difference is None


def test_template_need_update_record_with_all_fields():
    """Test TemplateNeedUpdateRecord initialization with all fields."""
    rec = TemplateNeedUpdateRecord(
        id=1, template_title="Test Template", slug="test-slug", chart_year=2023, template_year=2020
    )

    assert rec.id == 1
    assert rec.template_title == "Test Template"
    assert rec.slug == "test-slug"
    assert rec.chart_year == 2023
    assert rec.template_year == 2020
    assert rec.difference == 3  # 2023 - 2020


def test_template_need_update_record_difference_calculation():
    """Test difference calculation when both years are present."""
    rec = TemplateNeedUpdateRecord(
        id=1, template_title="Test Template", slug="test-slug", chart_year=2025, template_year=2020
    )

    assert rec.difference == 5  # 2025 - 2020


def test_template_need_update_record_difference_none_when_missing_years():
    """Test difference is None when either year is missing."""
    # Missing chart_year
    rec1 = TemplateNeedUpdateRecord(
        id=1, template_title="Test Template", slug="test-slug", chart_year=None, template_year=2020
    )
    assert rec1.difference is None

    # Missing template_year
    rec2 = TemplateNeedUpdateRecord(
        id=1, template_title="Test Template", slug="test-slug", chart_year=2025, template_year=None
    )
    assert rec2.difference is None

    # Both missing
    rec3 = TemplateNeedUpdateRecord(
        id=1, template_title="Test Template", slug="test-slug", chart_year=None, template_year=None
    )
    assert rec3.difference is None


def test_template_need_update_record_difference_with_zero_values():
    """Test difference calculation with zero values."""
    rec = TemplateNeedUpdateRecord(
        id=1, template_title="Test Template", slug="test-slug", chart_year=0, template_year=0
    )

    assert rec.difference == 0  # 0 - 0


def test_template_need_update_record_to_dict():
    """Test conversion to dictionary."""
    rec = TemplateNeedUpdateRecord(
        id=1, template_title="Test Template", slug="test-slug", chart_year=2023, template_year=2020
    )

    result = rec.to_dict()

    expected = {
        "id": 1,
        "template_title": "Test Template",
        "slug": "test-slug",
        "chart_year": 2023,
        "template_year": 2020,
        "difference": 3,
    }

    assert result == expected


def test_template_need_update_record_to_dict_with_none_values():
    """Test conversion to dictionary with None values."""
    rec = TemplateNeedUpdateRecord(id=1, template_title=None, slug=None, chart_year=None, template_year=None)

    result = rec.to_dict()

    expected = {
        "id": 1,
        "template_title": None,
        "slug": None,
        "chart_year": None,
        "template_year": None,
        "difference": None,
    }

    assert result == expected


def test_template_need_update_record_negative_difference():
    """Test negative difference when template year is greater than chart year."""
    rec = TemplateNeedUpdateRecord(
        id=1, template_title="Test Template", slug="test-slug", chart_year=2020, template_year=2023
    )

    assert rec.difference == -3  # 2020 - 2023
