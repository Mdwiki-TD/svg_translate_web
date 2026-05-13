"""Verification tests for CollectMainFilesWorker slug derivation."""

from __future__ import annotations
from src.main_app.jobs_workers.collect_main_files_worker import slugify_title

def test_slugify_title():
    """Test slugify_title with various inputs."""
    assert slugify_title("Template:OWID/Liberal political institutions row") == "liberal-political-institutions-row"
    assert slugify_title("Template:OWID/Daily meat consumption per person") == "daily-meat-consumption-per-person"
    assert slugify_title("Template:Some chart title") == "some-chart-title"
    assert slugify_title("Plain title") == "plain-title"
    assert slugify_title("Title With _ Underscores") == "title-with-underscores"
    assert slugify_title("Title With__Underscores") == "title-with-underscores"
    assert slugify_title("Title! with@ special# characters$") == "title-with-special-characters"
