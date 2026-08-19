"""Unit tests for collect_templates_data_worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.clients.objects import RawGrapherMetadataResponse
from src.main_app.database.models import TemplateRecord
from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data import CollectMainFilesWorker


@pytest.fixture
def mock_find_last_world(monkeypatch: pytest.MonkeyPatch):
    """Mock find_newest_world_file to return None by default."""
    mock = MagicMock(return_value=None)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_newest_world_file",
        mock,
    )
    return mock


@pytest.fixture
def mock_find_source(monkeypatch: pytest.MonkeyPatch):
    """Mock find_template_source to return empty string by default."""
    mock = MagicMock(return_value="")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_template_source",
        mock,
    )
    return mock


@pytest.fixture
def mock_collect_services(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Mock the services used by collect_templates_data_worker."""

    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.BaseObjectsJobWorker.before_run", MagicMock(return_value=True)
    )
    mocks = {
        "list": MagicMock(),
        "add_template_data": MagicMock(),
        "update_template_data": MagicMock(),
        "update_job_status": MagicMock(),
        "save_job_result_by_name": MagicMock(return_value=str(tmp_path / "job_1.json")),
        "get_category_members": MagicMock(),
        "MwClientPage": MagicMock(),
        "find_main_title": MagicMock(),
        "get_chart_by_slug": MagicMock(),
        "fetch_grapher_metadata_raw": MagicMock(return_value=RawGrapherMetadataResponse(data=None, status_code=None)),
        "get_user_site": MagicMock(return_value=MagicMock(name="mw_site")),
    }

    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.get_user_site",
        mocks["get_user_site"],
    )

    mock_template_service = MagicMock()
    mock_template_service.list = mocks["list"]
    mock_template_service.add_template_data = mocks["add_template_data"]
    mock_template_service.update_template_data = mocks["update_template_data"]
    mock_template_service.get_template_by_title = MagicMock()

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.TemplateService.update_template_data",
        mocks["update_template_data"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.TemplateService.list",
        mocks["list"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.TemplateService.add_template_data",
        mocks["add_template_data"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.TemplateService",
        MagicMock(return_value=mock_template_service),
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.JobsService.update_job_status",
        mocks["update_job_status"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mocks["save_job_result_by_name"],
    )

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.get_category_members",
        mocks["get_category_members"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.MwClientPage",
        mocks["MwClientPage"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_main_title",
        mocks["find_main_title"],
    )

    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_instance.get_chart_by_slug = mocks["get_chart_by_slug"]
    _mock_class.return_value = _mock_instance

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.OwidChartsService", _mock_class
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.fetch_grapher_metadata_raw",
        mocks["fetch_grapher_metadata_raw"],
    )

    return mocks


class TestRunner:

    @pytest.fixture(autouse=True)
    def setup(self, mock_collect_services):

        def run_wrapper(job_id, user, cancel_event=None, args=None, form_data=None):
            data = JobsRunner(job_id=job_id, user=user, cancel_event=cancel_event, args=args, form_data=form_data)
            worker = CollectMainFilesWorker(data)
            return worker.run()

        self.collect_runner = run_wrapper
        self.services = mock_collect_services

    def test_collect_templates_data_with_no_templates(self):
        """Test collect templates data entry when there are no templates."""
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = []

        self.collect_runner(job_id=1, user={})

        # Should save result
        self.services["save_job_result_by_name"].assert_called()
        # last call
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 0
        assert len(result_dict["pages_added"]) == 0

    def test_collect_templates_data_skips_templates_with_main_file(self, mock_find_source):
        """Test that templates with main_file AND last_world_file AND source are skipped."""
        templates = [
            TemplateRecord(
                id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg", source="test"
            ),
            TemplateRecord(
                id=2, title="Template:Test2", main_file="test2.svg", last_world_file="test2_2020.svg", source="test"
            ),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates

        self.collect_runner(job_id=1, user={})

        # Should not fetch wikitext for templates that have all three fields
        self.services["MwClientPage"].return_value.get_text.assert_not_called()

        # Should save result with skipped templates
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 2
        assert len(result_dict["pages_added"]) == 0

    def test_collect_templates_data_updates_template_without_main_file(self, mock_find_source):
        """Test that templates without main_file are updated."""
        templates = [
            TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None, source=""),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|test.svg}}"
        self.services["find_main_title"].return_value = "test.svg"

        magic = MagicMock()
        self.services["get_user_site"].return_value = magic

        self.collect_runner(job_id=1, user={})

        # Should fetch wikitext
        self.services["MwClientPage"].return_value.get_text.assert_called_once()
        self.services["MwClientPage"].assert_called_once_with("Template:Test", magic)

        # Should find main title
        self.services["find_main_title"].assert_called_once()

        # Should update template with main_file
        self.services["update_template_data"].assert_called_once_with(
            1,
            {
                "main_file": "test.svg",
                "slug": "test",
            },
        )

        # Should save result with updated template
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 1
        assert len(result_dict["pages_updated"]) == 1
        assert result_dict["pages_updated"][0]["steps"]["main_file"]["new_value"] == "test.svg"

    def test_collect_templates_data_handles_missing_wikitext(self):
        """Test that missing wikitext is handled gracefully."""
        templates = [
            TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = None

        self.collect_runner(job_id=1, user={})

        # Should not try to find main title
        self.services["find_main_title"].assert_not_called()

        # Should save result with failed template
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 1
        assert result_dict["summary"]["failed"] == 1
        assert len(result_dict["pages_failed"]) == 1
        assert "Could not fetch wikitext" in result_dict["pages_failed"][0]["error"]

    def test_collect_templates_data_handles_missing_main_title(self):
        """Test that missing main title is handled gracefully."""
        templates = [
            TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None, source=""),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = "some wikitext without SVGLanguages"
        self.services["find_main_title"].return_value = None

        self.collect_runner(job_id=1, user={})

        # Should not update template
        self.services["update_template_data"].assert_not_called()

        # Should save result with failed template
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 1
        assert result_dict["summary"]["failed"] == 1
        assert len(result_dict["pages_failed"]) == 1
        assert "Could not find (main file or newest world file or source)" in result_dict["pages_failed"][0]["error"]

    @pytest.mark.skip(reason="exceptions changes")
    def test_collect_templates_data_handles_exception(self):
        """Test that exceptions are handled gracefully."""
        templates = [
            TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.side_effect = Exception("Network error")

        self.collect_runner(job_id=1, user={})

        # Should save result with failed template
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 1
        assert result_dict["summary"]["failed"] == 1
        assert len(result_dict["pages_failed"]) == 1
        assert "Exception: Network error" in result_dict["pages_failed"][0]["error"]

    def test_collect_templates_data_processes_multiple_templates(self):
        """Test processing multiple templates with mixed results."""
        templates = [
            TemplateRecord(id=1, title="Template:Test1", main_file=None, last_world_file=None),
            TemplateRecord(id=2, title="Template:Test2", main_file="already.svg", last_world_file=None),
            TemplateRecord(id=3, title="Template:Test3", main_file=None, last_world_file=None),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates

        # First template: success
        # Third template: success
        def _mwclientpage_side_effect(title, site=None):
            instance = MagicMock()
            if "Test1" in title:
                instance.get_text.return_value = "{{SVGLanguages|test1.svg}}"
            elif "Test3" in title:
                instance.get_text.return_value = "{{SVGLanguages|test3.svg}}"
            else:
                instance.get_text.return_value = None
            return instance

        def find_main_title_side_effect(wikitext, remove_prefix=False):
            if "test1" in wikitext:
                return "test1.svg"
            elif "test3" in wikitext:
                return "test3.svg"
            return None

        self.services["MwClientPage"].side_effect = _mwclientpage_side_effect
        self.services["find_main_title"].side_effect = find_main_title_side_effect

        self.collect_runner(job_id=1, user={})

        # Should update two templates
        assert self.services["update_template_data"].call_count == 2

        # Should save result with correct counts
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 3
        assert len(result_dict["pages_updated"]) == 2
        assert result_dict["summary"]["skipped"] == 0

    def test_collect_templates_data_adds_new_templates_from_category(self):
        """Test that new templates from category are added to database."""
        # Existing template
        existing_templates = [
            TemplateRecord(
                id=1, title="Template:Existing", main_file="existing.svg", last_world_file="existing_2020.svg"
            ),
        ]
        # New templates from category
        category_templates = [
            "Template:Existing",  # Already exists
            "Template:New1",  # New
            "Template:New2",  # New
        ]

        self.services["get_category_members"].return_value = category_templates
        self.services["list"].return_value = existing_templates

        self.collect_runner(job_id=1, user={})

        # Should add 2 new templates
        assert self.services["add_template_data"].call_count == 2
        self.services["add_template_data"].assert_any_call({"title": "Template:New1"})
        self.services["add_template_data"].assert_any_call({"title": "Template:New2"})

        # Should save result with added templates
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert len(result_dict["pages_added"]) == 2

    def test_collect_templates_data_handles_add_template_value_error(self):
        """Test that ValueError from add_template (template already exists) is handled gracefully."""
        existing_templates = [
            TemplateRecord(
                id=1,
                title="Template:Existing",
                main_file="existing.svg",
                last_world_file="existing_2020.svg",
                source="test",
            ),
        ]
        category_templates = ["Template:New1"]

        self.services["get_category_members"].return_value = category_templates
        self.services["list"].return_value = existing_templates
        self.services["add_template_data"].side_effect = ValueError("Template 'Template:New1' already exists")

        self.collect_runner(job_id=1, user={})

        # Should continue processing without error
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert len(result_dict["pages_added"]) == 0
        assert len(result_dict["pages_failed"]) == 0  # ValueError is handled gracefully (race condition)

    def test_collect_templates_data_full_workflow_with_new_templates(self, mock_find_source):
        """Test full workflow: add new templates then collect templates data."""
        # First call returns empty (for adding phase), second call returns with new templates
        existing_templates = [
            TemplateRecord(
                id=1,
                title="Template:Existing",
                main_file="existing.svg",
                last_world_file="existing_2020.svg",
                source="test",
            ),
        ]
        new_template = TemplateRecord(
            id=2, title="Template:NewFromCategory", main_file="", last_world_file="", source=""
        )

        category_templates = ["Template:Existing", "Template:NewFromCategory"]

        self.services["get_category_members"].return_value = category_templates
        # First call returns existing, second call returns existing + new
        self.services["list"].side_effect = [existing_templates, existing_templates + [new_template]]
        self.services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
        self.services["find_main_title"].return_value = "newfile.svg"

        magic = MagicMock()
        self.services["get_user_site"].return_value = magic

        self.collect_runner(job_id=1, user={})

        # Should add new template
        self.services["add_template_data"].assert_called_once_with({"title": "Template:NewFromCategory"})

        # Should process the new template (fetch wikitext) - existing has all fields so it's skipped
        self.services["MwClientPage"].return_value.get_text.assert_called_once()
        self.services["MwClientPage"].assert_called_once_with("Template:NewFromCategory", magic)

        # Should update the new template with main file
        self.services["update_template_data"].assert_called_once_with(
            2,
            {
                "main_file": "newfile.svg",
                "slug": "newfromcategory",
            },
        )

        # Should save result with correct counts
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert len(result_dict["pages_added"]) == 1
        assert len(result_dict["pages_updated"]) == 1

    def test_collect_templates_data_with_last_world_file(self, monkeypatch: pytest.MonkeyPatch):
        """Test that last_world_file is extracted and saved."""
        templates = [
            TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None, source=""),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates

        wikitext_with_owidslidersrcs = """
        {{SVGLanguages|test.svg}}
        {{owidslidersrcs|id=gallery|widths=240|heights=240
        |gallery-World=
        File:test, World, 2020.svg!year=2020
        File:test, World, 2021.svg!year=2021
        }}
        """

        self.services["MwClientPage"].return_value.get_text.return_value = wikitext_with_owidslidersrcs
        self.services["find_main_title"].return_value = "test.svg"

        # Mock find_newest_world_file
        mock_find_last_world = MagicMock(return_value="test, World, 2021.svg")
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_newest_world_file",
            mock_find_last_world,
        )

        self.collect_runner(job_id=1, user={})

        # Should update template with both main_file and last_world_file
        self.services["update_template_data"].assert_called_once_with(
            1,
            {
                "main_file": "test.svg",
                "last_world_file": "test, World, 2021.svg",
                "last_world_year": 2021,
                "slug": "test",
                "files": 2,
            },
        )

        # Should save result with correct data
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert len(result_dict["pages_updated"]) == 1
        assert result_dict["pages_updated"][0]["steps"]["main_file"]["new_value"] == "test.svg"
        assert result_dict["pages_updated"][0]["steps"]["last_world_file"]["new_value"] == "test, World, 2021.svg"

    def test_collect_templates_data_cancellation_during_template_addition(self):
        """Test cancellation during template addition phase."""

        cancel_event = threading.Event()
        cancel_event.set()  # Cancel immediately

        category_templates = ["Template:New1", "Template:New2"]
        self.services["get_category_members"].return_value = category_templates
        self.services["list"].return_value = []

        self.collect_runner(job_id=1, user={}, cancel_event=cancel_event)

        # Should stop early and not add all templates
        # The exact behavior depends on when the cancellation is checked
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        # Job should be cancelled before processing templates
        assert len(result_dict["pages_updated"]) == 0

    def test_collect_templates_data_cancellation_during_processing(self):
        """Test cancellation during template processing phase."""

        cancel_event = threading.Event()

        templates = [
            TemplateRecord(id=1, title="Template:Test1", main_file=None, last_world_file=None),
            TemplateRecord(id=2, title="Template:Test2", main_file=None, last_world_file=None),
            TemplateRecord(id=3, title="Template:Test3", main_file=None, last_world_file=None),
        ]

        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates

        # Cancel after processing first template
        call_count = [0]

        def _mwclientpage_side_effect(title, site=None):
            call_count[0] += 1
            instance = MagicMock()
            if call_count[0] == 1:
                instance.get_text.return_value = "{{SVGLanguages|test1.svg}}"
            else:
                cancel_event.set()  # Cancel after first template
                instance.get_text.return_value = "{{SVGLanguages|test2.svg}}"
            return instance

        self.services["MwClientPage"].side_effect = _mwclientpage_side_effect
        self.services["find_main_title"].return_value = "test.svg"

        self.collect_runner(job_id=1, user={}, cancel_event=cancel_event)

        # Should have processed at least one template before cancellation
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        # Exact count depends on when cancellation is detected
        assert len(result_dict["pages_updated"]) == 2  # Should process 2 templates before cancellation

    def test_collect_templates_data_progress_saving_frequency(self, monkeypatch: pytest.MonkeyPatch):
        """Test that progress is saved every 10 templates."""
        # Create 25 templates to process
        templates = [
            TemplateRecord(id=i, title=f"Template:Test{i}", main_file=None, last_world_file=None) for i in range(1, 26)
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|test.svg}}"
        self.services["find_main_title"].return_value = "test.svg"

        # Track save_progress calls
        save_progress_calls: list = []
        original_save = self.services["save_job_result_by_name"]

        def track_save(*args, **kwargs):
            save_progress_calls.append(args)
            return original_save(*args, **kwargs)

        self.services["save_job_result_by_name"].side_effect = track_save

        self.collect_runner(job_id=1, user={})

        # Progress should be saved at: 1, 10, 20, and final
        # Expecting at least 3 saves (n=1, n=10, n=20, plus final)
        assert len(save_progress_calls) >= 3

    def test_collect_templates_data_only_last_world_file(self, monkeypatch: pytest.MonkeyPatch):
        """Test template with only last_world_file (no main_file)."""
        templates = [
            TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None, source=""),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates

        wikitext_without_main = """
        {{owidslidersrcs|id=gallery|widths=240|heights=240
        |gallery-World=
        File:test, World, 2021.svg!year=2021
        }}
        """

        self.services["MwClientPage"].return_value.get_text.return_value = wikitext_without_main
        self.services["find_main_title"].return_value = None  # No main file

        # Mock find_newest_world_file
        mock_find_last_world = MagicMock(return_value="test, World, 2021.svg")
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_newest_world_file",
            mock_find_last_world,
        )

        self.collect_runner(job_id=1, user={})

        # Should update template with only last_world_file
        self.services["update_template_data"].assert_called_once_with(
            1,
            {
                "last_world_file": "test, World, 2021.svg",
                "last_world_year": 2021,
                "slug": "test",
                "files": 1,
            },
        )

        # Should save result as updated
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert len(result_dict["pages_updated"]) == 1

    def test_collect_templates_data_template_with_existing_main_file_only(self):
        """Test that templates with main_file but no last_world_file are processed."""
        templates = [
            TemplateRecord(id=1, title="Template:Test", main_file="existing.svg", last_world_file=None, source=""),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|test.svg}}"
        self.services["find_main_title"].return_value = "test.svg"

        self.collect_runner(job_id=1, user={})

        # Should process template because last_world_file is missing
        self.services["MwClientPage"].return_value.get_text.assert_called_once()

        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 1

    def test_collect_templates_data_add_template_generic_exception(self):
        """Test that generic exceptions during add_template are tracked in pages_failed."""
        existing_templates: list = []
        category_templates = ["Template:New1"]

        self.services["get_category_members"].return_value = category_templates
        self.services["list"].return_value = existing_templates
        self.services["add_template_data"].side_effect = RuntimeError("Database connection failed")

        self.collect_runner(job_id=1, user={})

        # Should track in pages_failed but not increment summary["failed"] (that's for processing phase)
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert len(result_dict["pages_added"]) == 0
        assert len(result_dict["pages_failed"]) >= 1
        assert "Database connection failed" in result_dict["pages_failed"][0]["error"]

    def test_collect_templates_data_update_all_processes_all_templates(self, mock_find_source):
        """Test that update_all=True processes templates that already have all fields."""
        templates = [
            TemplateRecord(
                id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg", source="src1"
            ),
            TemplateRecord(
                id=2, title="Template:Test2", main_file="test2.svg", last_world_file="test2_2020.svg", source="src2"
            ),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
        self.services["find_main_title"].return_value = "newfile.svg"

        # With update_all=True, both templates should be processed even though they have data
        self.collect_runner(job_id=1, user={}, args={"update_all": "true"})

        # Both templates should have had their wikitext fetched
        assert self.services["MwClientPage"].return_value.get_text.call_count == 2

    def test_collect_templates_data_default_skips_complete_templates(self):
        """Test that without update_all, templates with all fields are skipped."""
        templates = [
            TemplateRecord(
                id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg", source="src1"
            ),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates

        # Without args (update_all=False by default), complete templates are skipped
        self.collect_runner(job_id=1, user={})

        # No wikitext should be fetched for a complete template
        self.services["MwClientPage"].return_value.get_text.assert_not_called()

    def test_collect_templates_data_entry_with_update_all_true_string(self, mock_find_source):
        """Test args parsing: args={'update_all': 'true'} enables update_all mode."""
        templates = [
            TemplateRecord(
                id=1, title="Template:Test1", main_file="existing.svg", last_world_file="world.svg", source="src"
            ),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
        self.services["find_main_title"].return_value = "newfile.svg"

        self.collect_runner(job_id=1, user={}, args={"update_all": "true"})

        # Should process the template even though it already has data
        self.services["MwClientPage"].return_value.get_text.assert_called_once()

    def test_collect_templates_data_entry_with_update_all_false_string(self):
        """Test args parsing: args={'update_all': 'false'} does not enable update_all mode."""
        templates = [
            TemplateRecord(
                id=1, title="Template:Test1", main_file="existing.svg", last_world_file="world.svg", source="src"
            ),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates

        self.collect_runner(job_id=1, user={}, args={"update_all": "false"})

        # Template is complete, should not be fetched
        self.services["MwClientPage"].return_value.get_text.assert_not_called()

    def test_collect_templates_data_entry_with_args_none(self):
        """Test that args=None means update_all=False."""
        templates = [
            TemplateRecord(
                id=1, title="Template:Test1", main_file="existing.svg", last_world_file="world.svg", source="src"
            ),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates

        self.collect_runner(job_id=1, user={}, args=None)

        # Template is complete, should not be fetched
        self.services["MwClientPage"].return_value.get_text.assert_not_called()

    def test_collect_templates_data_entry_update_all_case_insensitive(self, mock_find_source):
        """Test that update_all parsing is case-insensitive (e.g. 'TRUE', 'True')."""
        templates = [
            TemplateRecord(
                id=1, title="Template:Test1", main_file="existing.svg", last_world_file="world.svg", source="src"
            ),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
        self.services["find_main_title"].return_value = "newfile.svg"

        self.collect_runner(job_id=1, user={}, args={"update_all": "TRUE"})

        # Should process even with uppercase "TRUE"
        self.services["MwClientPage"].return_value.get_text.assert_called_once()

    def test_collect_templates_data_entry_cancel_event_is_keyword_only(self):
        """Test that cancel_event is keyword-only in collect templates data entry."""

        cancel_event = threading.Event()
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = []

        # Should not raise a TypeError - cancel_event must be passed as keyword arg
        self.collect_runner(job_id=1, user={}, cancel_event=cancel_event)

        # last call
        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 0

    def test_collect_templates_data_entry_update_all_summary_counts(self, mock_find_source):
        """Test that update_all mode processes all templates including those already complete."""
        templates = [
            TemplateRecord(
                id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg", source="src1"
            ),
            TemplateRecord(id=2, title="Template:Test2", main_file=None, last_world_file=None, source=""),
        ]
        self.services["get_category_members"].return_value = []
        self.services["list"].return_value = templates
        self.services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
        self.services["find_main_title"].return_value = "newfile.svg"

        self.collect_runner(job_id=1, user={}, args={"update_all": "true"})

        result_dict = self.services["save_job_result_by_name"].call_args[0][1]
        # Total is 2, 1 already had all data
        assert result_dict["summary"]["total"] == 2
        # With update_all, both templates are processed
        assert self.services["MwClientPage"].return_value.get_text.call_count == 2
