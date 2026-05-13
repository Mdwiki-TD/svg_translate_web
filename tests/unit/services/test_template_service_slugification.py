"""Verification tests for template_service slugification."""

from __future__ import annotations
from src.main_app.services.template_service import slugify_title, ensure_last_world_year

def test_slugify_title():
    """Test slugify_title with various inputs."""
    assert slugify_title("Template:OWID/Liberal political institutions row") == "liberal-political-institutions-row"
    assert slugify_title("Template:OWID/Daily meat consumption per person") == "daily-meat-consumption-per-person"
    assert slugify_title("Template:Some chart title") == "some-chart-title"
    assert slugify_title("Plain title") == "plain-title"
    assert slugify_title("Title With _ Underscores") == "title-with-underscores"
    # The logic replaces _ with - and then removes multiple hyphens
    assert slugify_title("Title With__Underscores") == "title-with-underscores"
    assert slugify_title("Title! with@ special# characters$") == "title-with-special-characters"

def test_ensure_last_world_year_slug_from_url():
    """Test extraction of slug from /grapher/ URL."""
    data = {
        "title": "Some Title",
        "slug": "https://ourworldindata.org/grapher/some-chart-slug?tab=map"
    }
    processed = ensure_last_world_year(data)
    assert processed["slug"] == "some-chart-slug"

def test_ensure_last_world_year_slug_from_source():
    """Test extraction of slug from source URL if slug is missing."""
    data = {
        "title": "Some Title",
        "slug": "",
        "source": "https://ourworldindata.org/grapher/another-chart-slug"
    }
    processed = ensure_last_world_year(data)
    assert processed["slug"] == "another-chart-slug"

def test_ensure_last_world_year_slug_from_title_fallback():
    """Test derivation of slug from title for Explorer URLs."""
    data = {
        "title": "Template:OWID/Liberal political institutions row",
        "slug": "",
        "source": "https://ourworldindata.org/explorers/democracy?Dataset=Regimes+of+the+World&Metric=%C2%ADLiberal+democracy&Sub-metric=%C2%ADLiberal+political+institution"
    }
    processed = ensure_last_world_year(data)
    assert processed["slug"] == "liberal-political-institutions-row"

def test_ensure_last_world_year_no_title_no_slug():
    """Test with no title and no slug (should remain unchanged or empty)."""
    data = {
        "source": "https://example.com"
    }
    processed = ensure_last_world_year(data)
    assert "slug" not in processed or processed["slug"] == ""
