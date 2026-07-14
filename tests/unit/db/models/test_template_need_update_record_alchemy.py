from __future__ import annotations

from src.main_app.db.models.views import TemplateNeedUpdateView


def test_template_need_update_record_initialization():
    """Test TemplateNeedUpdateView initialization with required fields."""
    rec = TemplateNeedUpdateView(template_id=1)

    assert rec.template_id == 1
    assert rec.template_title is None
    assert rec.slug is None
    assert rec.max_time is None
    assert rec.last_world_year is None
    assert rec.to_dict()["difference"] == 0


def test_template_need_update_record_with_all_fields():
    """Test TemplateNeedUpdateView initialization with all fields."""
    rec = TemplateNeedUpdateView(
        template_id=1, template_title="Test Template", slug="test-slug", max_time=2023, last_world_year=2020
    )

    assert rec.template_id == 1
    assert rec.template_title == "Test Template"
    assert rec.slug == "test-slug"
    assert rec.max_time == 2023
    assert rec.last_world_year == 2020
    assert rec.to_dict()["difference"] == 3  # 2023 - 2020


def test_template_need_update_record_difference_calculation():
    """Test difference calculation when both years are present."""
    rec = TemplateNeedUpdateView(
        template_id=1, template_title="Test Template", slug="test-slug", max_time=2025, last_world_year=2020
    )

    assert rec.to_dict()["difference"] == 5  # 2025 - 2020


def test_template_need_update_record_difference_none_when_missing_years():
    """Test difference is None when either year is missing."""
    # Missing max_time
    rec1 = TemplateNeedUpdateView(
        template_id=1, template_title="Test Template", slug="test-slug", max_time=None, last_world_year=2020
    )
    assert rec1.to_dict()["difference"] == 0

    # Missing last_world_year
    rec2 = TemplateNeedUpdateView(
        template_id=1, template_title="Test Template", slug="test-slug", max_time=2025, last_world_year=None
    )
    assert rec2.to_dict()["difference"] == 0

    # Both missing
    rec3 = TemplateNeedUpdateView(
        template_id=1, template_title="Test Template", slug="test-slug", max_time=None, last_world_year=None
    )
    assert rec3.to_dict()["difference"] == 0


def test_template_need_update_record_difference_with_zero_values():
    """Test difference calculation with zero values."""
    rec = TemplateNeedUpdateView(
        template_id=1, template_title="Test Template", slug="test-slug", max_time=0, last_world_year=0
    )

    assert rec.to_dict()["difference"] == 0  # 0 - 0


def test_template_need_update_record_to_dict():
    """Test conversion to dictionary."""
    rec = TemplateNeedUpdateView(
        template_id=1, template_title="Test Template", slug="test-slug", max_time=2023, last_world_year=2020
    )

    result = rec.to_dict()

    expected = {
        "template_id": 1,
        "template_title": "Test Template",
        "owid_variable_id": "",
        "slug": "test-slug",
        "max_time": 2023,
        "last_world_year": 2020,
        "difference": 3,
    }

    assert result == expected


def test_template_need_update_record_to_dict_with_none_values():
    """Test conversion to dictionary with None values."""
    rec = TemplateNeedUpdateView(template_id=1, template_title=None, slug=None, max_time=None, last_world_year=None)

    result = rec.to_dict()

    expected = {
        "template_id": 1,
        "template_title": None,
        "owid_variable_id": "",
        "slug": None,
        "max_time": None,
        "last_world_year": None,
        "difference": 0,
    }

    assert result == expected


def test_template_need_update_record_negative_difference():
    """Test negative difference when template year is greater than chart year."""
    rec = TemplateNeedUpdateView(
        template_id=1, template_title="Test Template", slug="test-slug", max_time=2020, last_world_year=2023
    )

    assert rec.to_dict()["difference"] == -3  # 2020 - 2023
