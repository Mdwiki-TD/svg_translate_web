from __future__ import annotations

from src.main_app.db.models.templates import TemplateRecord
from src.main_app.db.templates_utils import ensure_template_data_record


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
    rec = ensure_template_data_record(rec)

    assert rec.to_dict()["slug"] == "health-expenditure"


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
    rec = ensure_template_data_record(rec)

    assert rec.to_dict()["slug"] == "health-expenditure"


def test_template_record_last_world_year_from_cropped_file():
    """Test last_world_year extraction from filename."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file="File:Health-expenditure-government-expenditure,World,2022 (cropped).svg",
    )

    rec = ensure_template_data_record(rec)
    # Year should be extracted from filename
    assert rec.to_dict()["last_world_year"] == 2022


def test_template_record_last_world_year_from_file():
    """Test last_world_year extraction from filename."""
    rec = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="test.svg",
        last_world_file="File:Health-expenditure-government-expenditure,World, 2022.svg",
    )

    # Year should be extracted from filename
    rec = ensure_template_data_record(rec)

    assert rec.to_dict()["last_world_year"] == 2022
