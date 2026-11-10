"""
Tests for TemplateData usage in the collect_templates_data worker.
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.database.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker import (
    CollectMainFilesWorker,
    TemplateData,
)
from src.main_app.jobs_workers.objects import JobsRunner

WORKER_PATH = "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker"

# The db.models.TemplateRecord.__init__ also uses hasattr(self, key) but
# works because SQLAlchemy declarative base sets up descriptors on the class.
# TemplateData (a plain dataclass) does NOT have that, so __init__ must
# setattr unconditionally (hasattr always returns False at init time).


@pytest.fixture
def patch_extractors(monkeypatch: pytest.MonkeyPatch):
    """Factory fixture: patch every extractor the worker calls with fixed return values."""

    def _apply(
        *,
        main_title: str | None = "file.svg",
        world_file: str | None = "world.svg",
        year: int | None = 2024,
        source: str | None = "src",
        slug: str | None = "test-slug",
    ) -> None:
        monkeypatch.setattr(
            f"{WORKER_PATH}.MainTitleFinder.find_main_title",
            lambda text, remove_prefix=False: main_title,
        )
        monkeypatch.setattr(
            f"{WORKER_PATH}.SlidersGalleryReader.find_newest_world_file",
            lambda text, remove_prefix=False: world_file,
        )
        monkeypatch.setattr(
            f"{WORKER_PATH}.SlidersGalleryReader.find_newest_year",
            lambda text: year,
        )
        monkeypatch.setattr(
            f"{WORKER_PATH}.OwidSourceFinder.find_template_source",
            lambda text, check_grapher=False: source,
        )
        monkeypatch.setattr(
            f"{WORKER_PATH}.OneFileProcessor._load_slug",
            lambda self, title, slug_arg, source_arg: slug,
        )

    return _apply


class TestTemplateDataConstruction:
    """TemplateData.__init__ strips File: prefix and sets all fields."""

    def test_creates_instance_with_all_fields(self):
        data = TemplateData(
            id=1,
            title="Template:Test",
            main_file="test.svg",
            last_world_file="test_2020.svg",
            last_world_year=2020,
            slug="test",
            source="https://example.org/grapher/test",
        )
        assert data.id == 1
        assert data.title == "Template:Test"
        assert data.main_file == "test.svg"
        assert data.last_world_file == "test_2020.svg"
        assert data.last_world_year == 2020
        assert data.slug == "test"
        assert data.source == "https://example.org/grapher/test"

    def test_strips_file_prefix_from_main_file(self):
        data = TemplateData(main_file="File:test.svg")
        assert data.main_file == "test.svg"

    def test_strips_file_prefix_from_last_world_file(self):
        data = TemplateData(last_world_file="File:world.svg")
        assert data.last_world_file == "world.svg"

    def test_does_not_strip_empty_values(self):
        data = TemplateData(main_file="", last_world_file="")
        assert data.main_file == ""

    def test_accepts_empty_kwargs(self):
        data = TemplateData()
        assert data is not None

    def test_preserves_non_file_fields(self):
        data = TemplateData(
            id=42,
            title="Template:OWID/Test",
            slug="test-slug",
            source="https://example.org",
        )
        assert data.id == 42
        assert data.title == "Template:OWID/Test"
        assert data.slug == "test-slug"
        assert data.source == "https://example.org"


class TestTemplateRecordToTemplateDataConversion:
    """start_process converts TemplateRecord to TemplateData."""

    def test_conversion_preserves_all_fields(self, mock_base_worker):
        record = TemplateRecord(
            id=5,
            title="Template:Test",
            main_file="test.svg",
            last_world_file="test_2020.svg",
            last_world_year=2020,
            slug="test",
            source="https://example.org",
        )
        data = TemplateData(
            id=record.id,
            title=record.title,
            main_file=record.main_file,
            last_world_file=record.last_world_file,
            last_world_year=record.last_world_year,
            slug=record.slug,
            source=record.source,
        )
        assert data.id == record.id
        assert data.title == record.title
        assert data.main_file == record.main_file
        assert data.last_world_file == record.last_world_file
        assert data.last_world_year == record.last_world_year
        assert data.slug == record.slug
        assert data.source == record.source

    def test_conversion_strips_file_prefix(self):
        record = TemplateRecord(
            id=1,
            title="Template:Test",
            main_file="File:test.svg",
            last_world_file="File:test_2020.svg",
        )
        data = TemplateData(
            id=record.id,
            title=record.title,
            main_file=record.main_file,
            last_world_file=record.last_world_file,
        )
        assert data.main_file == "test.svg"
        assert data.last_world_file == "test_2020.svg"


class TestProcessOneItemWithTemplateData:
    """_process_one_item compares extracted values against TemplateData attributes."""

    @pytest.fixture
    def worker(self, mock_base_worker, monkeypatch, patch_extractors):
        w = CollectMainFilesWorker(
            JobsRunner(
                job_id=1,
                user={},
                cancel_event=threading.Event(),
            )
        )
        w.site = MagicMock()
        w.template_service = MagicMock()
        monkeypatch.setattr(
            f"{WORKER_PATH}.MwClientPage",
            lambda title, site: MagicMock(get_text=MagicMock(return_value="wikitext")),
        )
        # Default extracted values; individual tests override via patch_extractors(...)
        patch_extractors()
        return w

    def test_updates_template_when_data_differs_from_template_data(self, worker):
        template = TemplateData(
            id=1,
            title="T",
            main_file="old.svg",
            last_world_file="old_world.svg",
            last_world_year=2020,
            slug="x",
            source="y",
        )
        worker.template_service.update_template_data = MagicMock()
        result = worker._process_one_item(template)
        assert result is True

    def test_skips_template_when_all_data_matches(self, worker):
        template = TemplateData(
            id=1,
            title="T",
            main_file="file.svg",
            last_world_file="world.svg",
            last_world_year=2024,
            slug="test-slug",
            source="src",
        )
        result = worker._process_one_item(template)
        assert result is False

    def test_marks_failed_when_no_data_extracted(self, worker, patch_extractors):
        patch_extractors(main_title=None, world_file=None, year=None, source=None, slug=None)
        template = TemplateData(id=1, title="T", main_file=None, last_world_file=None, slug="", source="")
        result = worker._process_one_item(template)
        assert result is False
        assert len(worker.result.pages_failed) == 1

    def test_slug_updated_from_extracted(self, worker, patch_extractors):
        worker.template_service.update_template_data = MagicMock()
        patch_extractors(slug="new-slug")
        template = TemplateData(
            id=1, title="T", main_file=None, last_world_file=None, last_world_year=None, slug="old-slug", source=""
        )
        result = worker._process_one_item(template)
        assert result is True
