from __future__ import annotations


from src.main_app.db.models.views import TemplateNeedUpdateRecord


def test_template_need_update_record_initialization():
    """Test TemplateNeedUpdateRecord initialization with required fields."""
    rec = TemplateNeedUpdateRecord(template_id=1)

    assert rec.template_id == 1
    assert rec.template_title is None
    assert rec.slug is None
    assert rec.chart_year is None
    assert rec.last_world_year is None
    assert rec.difference is None


def test_template_need_update_record_with_all_fields():
    """Test TemplateNeedUpdateRecord initialization with all fields."""
    rec = TemplateNeedUpdateRecord(
        template_id=1, template_title="Test Template", slug="test-slug", chart_year=2023, last_world_year=2020
    )

    assert rec.template_id == 1
    assert rec.template_title == "Test Template"
    assert rec.slug == "test-slug"
    assert rec.chart_year == 2023
    assert rec.last_world_year == 2020
    assert rec.difference == 3  # 2023 - 2020


def test_template_need_update_record_difference_calculation():
    """Test difference calculation when both years are present."""
    rec = TemplateNeedUpdateRecord(
        template_id=1, template_title="Test Template", slug="test-slug", chart_year=2025, last_world_year=2020
    )

    assert rec.difference == 5  # 2025 - 2020


def test_template_need_update_record_difference_none_when_missing_years():
    """Test difference is None when either year is missing."""
    # Missing chart_year
    rec1 = TemplateNeedUpdateRecord(
        template_id=1, template_title="Test Template", slug="test-slug", chart_year=None, last_world_year=2020
    )
    assert rec1.difference is None

    # Missing last_world_year
    rec2 = TemplateNeedUpdateRecord(
        template_id=1, template_title="Test Template", slug="test-slug", chart_year=2025, last_world_year=None
    )
    assert rec2.difference is None

    # Both missing
    rec3 = TemplateNeedUpdateRecord(
        template_id=1, template_title="Test Template", slug="test-slug", chart_year=None, last_world_year=None
    )
    assert rec3.difference is None


def test_template_need_update_record_difference_with_zero_values():
    """Test difference calculation with zero values."""
    rec = TemplateNeedUpdateRecord(
        template_id=1, template_title="Test Template", slug="test-slug", chart_year=0, last_world_year=0
    )

    assert rec.difference == 0  # 0 - 0


def test_template_need_update_record_to_dict():
    """Test conversion to dictionary."""
    rec = TemplateNeedUpdateRecord(
        template_id=1, template_title="Test Template", slug="test-slug", chart_year=2023, last_world_year=2020
    )

    result = rec.to_dict()

    expected = {
        "template_id": 1,
        "template_title": "Test Template",
        "slug": "test-slug",
        "chart_year": 2023,
        "last_world_year": 2020,
        "difference": 3,
    }

    assert result == expected


def test_template_need_update_record_to_dict_with_none_values():
    """Test conversion to dictionary with None values."""
    rec = TemplateNeedUpdateRecord(template_id=1, template_title=None, slug=None, chart_year=None, last_world_year=None)

    result = rec.to_dict()

    expected = {
        "template_id": 1,
        "template_title": None,
        "slug": None,
        "chart_year": None,
        "last_world_year": None,
        "difference": None,
    }

    assert result == expected


def test_template_need_update_record_negative_difference():
    """Test negative difference when template year is greater than chart year."""
    rec = TemplateNeedUpdateRecord(
        template_id=1, template_title="Test Template", slug="test-slug", chart_year=2020, last_world_year=2023
    )

    assert rec.difference == -3  # 2020 - 2023
