from __future__ import annotations

import pytest

from src.main_app.shared.models.template_record import TemplateRecord
from src.main_app.utils.wikitext.titles_utils import match_last_world_year


def test_template_record_initialization():
    """Test TemplateRecord initialization with required fields."""
    rec = TemplateRecord(id=1, title="Test Template", main_file="test.svg", last_world_file=None)

    assert rec.id == 1
    assert rec.title == "Test Template"
    assert rec.main_file == "test.svg"
    assert rec.last_world_file is None
    assert rec.last_world_year is None
    assert rec.source is None
    assert rec.slug is None
    assert rec.created_at is None
    assert rec.updated_at is None


def test_template_record_with_all_fields():
    """Test TemplateRecord initialization with all fields."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file="test_world.svg",
        last_world_year=2023,
        source="https://example.com",
        slug="test-slug",
        created_at="2023-01-01",
        updated_at="2023-01-02",
    )

    assert rec.id == 1
    assert rec.title == "Test Template"
    assert rec.main_file == "test.svg"
    assert rec.last_world_file == "test_world.svg"
    assert rec.last_world_year == 2023
    assert rec.source == "https://example.com"
    assert rec.slug == "test-slug"
    assert rec.created_at == "2023-01-01"
    assert rec.updated_at == "2023-01-02"


def test_template_record_slug_generation():
    """Test slug generation for OWID source URLs."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file=None,
        source="https://ourworldindata.org/grapher/health-expenditure",
    )

    # Slug should be generated from source
    assert rec.slug == "health-expenditure"


def test_template_record_slug_generation_with_query_params():
    """Test slug generation with query parameters in source URL."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file=None,
        source="https://ourworldindata.org/grapher/health-expenditure?tab=chart",
    )

    # Slug should exclude query parameters
    assert rec.slug == "health-expenditure"


def test_template_record_no_slug_generation():
    """Test that slug is not generated for non-OWID sources."""
    rec = TemplateRecord(
        id=1, title="Test Template", main_file="test.svg", last_world_file=None, source="https://example.com/some-chart"
    )

    # Slug should remain None for non-OWID sources
    assert rec.slug is None


def test_template_record_slug_already_set():
    """Test that existing slug is not overwritten."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file=None,
        source="https://ourworldindata.org/grapher/health-expenditure",
        slug="existing-slug",
    )

    # Existing slug should be preserved
    assert rec.slug == "existing-slug"


def test_template_record_last_world_year_from_cropped_file():
    """Test last_world_year extraction from filename."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file="File:Health-expenditure-government-expenditure,World,2022 (cropped).svg",
    )

    # Year should be extracted from filename
    assert rec.last_world_year == 2022


def test_template_record_last_world_year_from_file():
    """Test last_world_year extraction from filename."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file="File:Health-expenditure-government-expenditure,World, 2022.svg",
    )

    # Year should be extracted from filename
    assert rec.last_world_year == 2022


def test_template_record_last_world_year_none():
    """Test last_world_year remains None when no file."""
    rec = TemplateRecord(id=1, title="Test Template", main_file="test.svg", last_world_file=None)

    # Year should remain None
    assert rec.last_world_year is None


def test_template_record_to_dict():
    """Test conversion to dictionary."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file="test_world.svg",
        last_world_year=2023,
        source="https://example.com",
        slug="test-slug",
        created_at="2023-01-01",
        updated_at="2023-01-02",
    )

    result = rec.to_dict()

    expected = {
        "id": 1,
        "title": "Test Template",
        "main_file": "test.svg",
        "last_world_file": "test_world.svg",
        "last_world_year": 2023,
        "source": "https://example.com",
        "slug": "test-slug",
        "created_at": "2023-01-01",
        "updated_at": "2023-01-02",
    }

    assert result == expected


def test_template_record_to_dict_with_none_values():
    """Test conversion to dictionary with None values."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file=None,
        last_world_year=None,
        source=None,
        slug=None,
        created_at=None,
        updated_at=None,
    )

    result = rec.to_dict()

    expected = {
        "id": 1,
        "title": "Test Template",
        "main_file": "test.svg",
        "last_world_file": None,
        "last_world_year": None,
        "source": None,
        "slug": None,
        "created_at": None,
        "updated_at": None,
    }

    assert result == expected
