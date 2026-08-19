"""
Tests for TemplateInfos in the collect_templates_data objects.
"""

from __future__ import annotations

from src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.objects import TemplateInfos
from src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker import (
    TemplateData,
)


class TestLoadTempInfoFromTemplateData:
    """TemplateInfos.from_template reads attributes from TemplateData objects."""

    def test_loads_basic_info(self) -> None:
        template = TemplateData(
            id=10,
            title="Template:Test",
            main_file=None,
            last_world_file=None,
            slug="",
            source="",
        )
        info = TemplateInfos.from_template(template)
        assert info.id == 10
        assert info.title == "Template:Test"
        assert info.status == ""

    def test_preserves_existing_main_file_in_step(self) -> None:
        template = TemplateData(
            id=1,
            title="T",
            main_file="existing.svg",
            last_world_file=None,
            slug="",
            source="",
        )
        info = TemplateInfos.from_template(template)
        assert info.steps.main_file.value == "existing.svg"

    def test_preserves_existing_last_world_file_in_step(self) -> None:
        template = TemplateData(
            id=1,
            title="T",
            main_file=None,
            last_world_file="world.svg",
            slug="",
            source="",
        )
        info = TemplateInfos.from_template(template)
        assert info.steps.last_world_file.value == "world.svg"

    def test_preserves_source_and_slug(self) -> None:
        template = TemplateData(
            id=1,
            title="T",
            main_file=None,
            last_world_file=None,
            slug="my-slug",
            source="src",
        )
        info = TemplateInfos.from_template(template)
        assert info.steps.source.value == "src"
        assert info.steps.slug.value == "my-slug"
