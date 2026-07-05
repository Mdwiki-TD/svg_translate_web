"""Unit tests for collect_templates_data_worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data import runner


def test_collect_templates_data_with_no_templates(mock_services):
    """Test collect_templates_data_entry when there are no templates."""
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = []

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should save result
    mock_services["save_job_result_by_name"].assert_called()
    # last call
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0
    assert len(result_dict["pages_added"]) == 0


def test_collect_templates_data_skips_templates_with_main_file(mock_services, mock_find_source):
    """Test that templates with main_file AND last_world_file AND source are skipped."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg", source="test"
        ),
        TemplateRecord(
            id=2, title="Template:Test2", main_file="test2.svg", last_world_file="test2_2020.svg", source="test"
        ),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should not fetch wikitext for templates that have all three fields
    mock_services["MwClientPage"].return_value.get_text.assert_not_called()

    # Should save result with skipped templates
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 2
    assert len(result_dict["pages_added"]) == 0


def test_collect_templates_data_updates_template_without_main_file(mock_services, mock_find_source):
    """Test that templates without main_file are updated."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None, source=""),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|test.svg}}"
    mock_services["find_main_title"].return_value = "test.svg"

    magic = MagicMock()
    mock_services["get_user_site"].return_value = magic

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should fetch wikitext
    mock_services["MwClientPage"].return_value.get_text.assert_called_once()
    mock_services["MwClientPage"].assert_called_once_with("Template:Test", magic)

    # Should find main title
    mock_services["find_main_title"].assert_called_once()

    # Should update template with main_file
    mock_services["update_template_data"].assert_called_once_with(
        1,
        {
            "main_file": "test.svg",
            "slug": "test",
        },
    )

    # Should save result with updated template
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert len(result_dict["pages_updated"]) == 1
    assert result_dict["pages_updated"][0]["steps"]["main_file"]["new_value"] == "test.svg"


def test_collect_templates_data_handles_missing_wikitext(mock_services):
    """Test that missing wikitext is handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = None

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should not try to find main title
    mock_services["find_main_title"].assert_not_called()

    # Should save result with failed template
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert result_dict["summary"]["failed"] == 1
    assert len(result_dict["pages_failed"]) == 1
    assert "Could not fetch wikitext" in result_dict["pages_failed"][0]["error"]


def test_collect_templates_data_handles_missing_main_title(mock_services):
    """Test that missing main title is handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None, source=""),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = "some wikitext without SVGLanguages"
    mock_services["find_main_title"].return_value = None

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should not update template
    mock_services["update_template_data"].assert_not_called()

    # Should save result with failed template
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert result_dict["summary"]["failed"] == 1
    assert len(result_dict["pages_failed"]) == 1
    assert "Could not find (main file or newest world file or source)" in result_dict["pages_failed"][0]["error"]


@pytest.mark.skip(reason="exceptions changes")
def test_collect_templates_data_handles_exception(mock_services):
    """Test that exceptions are handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.side_effect = Exception("Network error")

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should save result with failed template
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert result_dict["summary"]["failed"] == 1
    assert len(result_dict["pages_failed"]) == 1
    assert "Exception: Network error" in result_dict["pages_failed"][0]["error"]


def test_collect_templates_data_processes_multiple_templates(mock_services):
    """Test processing multiple templates with mixed results."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", main_file=None, last_world_file=None),
        TemplateRecord(id=2, title="Template:Test2", main_file="already.svg", last_world_file=None),
        TemplateRecord(id=3, title="Template:Test3", main_file=None, last_world_file=None),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates

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

    mock_services["MwClientPage"].side_effect = _mwclientpage_side_effect
    mock_services["find_main_title"].side_effect = find_main_title_side_effect

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should update two templates
    assert mock_services["update_template_data"].call_count == 2

    # Should save result with correct counts
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 3
    assert len(result_dict["pages_updated"]) == 2
    assert result_dict["summary"]["skipped"] == 0


def test_collect_templates_data_adds_new_templates_from_category(mock_services):
    """Test that new templates from category are added to database."""
    # Existing template
    existing_templates = [
        TemplateRecord(id=1, title="Template:Existing", main_file="existing.svg", last_world_file="existing_2020.svg"),
    ]
    # New templates from category
    category_templates = [
        "Template:Existing",  # Already exists
        "Template:New1",  # New
        "Template:New2",  # New
    ]

    mock_services["get_category_members"].return_value = category_templates
    mock_services["list_templates"].return_value = existing_templates

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should add 2 new templates
    assert mock_services["add_template_data"].call_count == 2
    mock_services["add_template_data"].assert_any_call({"title": "Template:New1"})
    mock_services["add_template_data"].assert_any_call({"title": "Template:New2"})

    # Should save result with added templates
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_added"]) == 2


def test_collect_templates_data_handles_add_template_value_error(mock_services):
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

    mock_services["get_category_members"].return_value = category_templates
    mock_services["list_templates"].return_value = existing_templates
    mock_services["add_template_data"].side_effect = ValueError("Template 'Template:New1' already exists")

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should continue processing without error
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_added"]) == 0
    assert len(result_dict["pages_failed"]) == 0  # ValueError is handled gracefully (race condition)


def test_collect_templates_data_full_workflow_with_new_templates(mock_services, mock_find_source):
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
    new_template = TemplateRecord(id=2, title="Template:NewFromCategory", main_file="", last_world_file="", source="")

    category_templates = ["Template:Existing", "Template:NewFromCategory"]

    mock_services["get_category_members"].return_value = category_templates
    # First call returns existing, second call returns existing + new
    mock_services["list_templates"].side_effect = [existing_templates, existing_templates + [new_template]]
    mock_services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
    mock_services["find_main_title"].return_value = "newfile.svg"

    magic = MagicMock()
    mock_services["get_user_site"].return_value = magic

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should add new template
    mock_services["add_template_data"].assert_called_once_with({"title": "Template:NewFromCategory"})

    # Should process the new template (fetch wikitext) - existing has all fields so it's skipped
    mock_services["MwClientPage"].return_value.get_text.assert_called_once()
    mock_services["MwClientPage"].assert_called_once_with("Template:NewFromCategory", magic)

    # Should update the new template with main file
    mock_services["update_template_data"].assert_called_once_with(
        2,
        {
            "main_file": "newfile.svg",
            "slug": "newfromcategory",
        },
    )

    # Should save result with correct counts
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_added"]) == 1
    assert len(result_dict["pages_updated"]) == 1


def test_collect_templates_data_with_last_world_file(mock_services, monkeypatch: pytest.MonkeyPatch):
    """Test that last_world_file is extracted and saved."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None, source=""),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates

    wikitext_with_owidslidersrcs = """
    {{SVGLanguages|test.svg}}
    {{owidslidersrcs|id=gallery|widths=240|heights=240
    |gallery-World=
    File:test, World, 2020.svg!year=2020
    File:test, World, 2021.svg!year=2021
    }}
    """

    mock_services["MwClientPage"].return_value.get_text.return_value = wikitext_with_owidslidersrcs
    mock_services["find_main_title"].return_value = "test.svg"

    # Mock find_newest_world_file
    mock_find_last_world = MagicMock(return_value="test, World, 2021.svg")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_newest_world_file",
        mock_find_last_world,
    )

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should update template with both main_file and last_world_file
    mock_services["update_template_data"].assert_called_once_with(
        1,
        {
            "main_file": "test.svg",
            "last_world_file": "test, World, 2021.svg",
            "last_world_year": 2021,
            "slug": "test",
        },
    )

    # Should save result with correct data
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_updated"]) == 1
    assert result_dict["pages_updated"][0]["steps"]["main_file"]["new_value"] == "test.svg"
    assert result_dict["pages_updated"][0]["steps"]["last_world_file"]["new_value"] == "test, World, 2021.svg"


def test_collect_templates_data_cancellation_during_template_addition(mock_services):
    """Test cancellation during template addition phase."""
    import threading

    cancel_event = threading.Event()
    cancel_event.set()  # Cancel immediately

    category_templates = ["Template:New1", "Template:New2"]
    mock_services["get_category_members"].return_value = category_templates
    mock_services["list_templates"].return_value = []

    runner.collect_templates_data_entry(job_id=1, user=None, cancel_event=cancel_event)

    # Should stop early and not add all templates
    # The exact behavior depends on when the cancellation is checked
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    # Job should be cancelled before processing templates
    assert len(result_dict["pages_updated"]) == 0


def test_collect_templates_data_cancellation_during_processing(mock_services):
    """Test cancellation during template processing phase."""
    import threading

    cancel_event = threading.Event()

    templates = [
        TemplateRecord(id=1, title="Template:Test1", main_file=None, last_world_file=None),
        TemplateRecord(id=2, title="Template:Test2", main_file=None, last_world_file=None),
        TemplateRecord(id=3, title="Template:Test3", main_file=None, last_world_file=None),
    ]

    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates

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

    mock_services["MwClientPage"].side_effect = _mwclientpage_side_effect
    mock_services["find_main_title"].return_value = "test.svg"

    runner.collect_templates_data_entry(job_id=1, user=None, cancel_event=cancel_event)

    # Should have processed at least one template before cancellation
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    # Exact count depends on when cancellation is detected
    assert len(result_dict["pages_updated"]) == 2  # Should process 2 templates before cancellation


def test_collect_templates_data_progress_saving_frequency(mock_services, monkeypatch: pytest.MonkeyPatch):
    """Test that progress is saved every 10 templates."""
    # Create 25 templates to process
    templates = [
        TemplateRecord(id=i, title=f"Template:Test{i}", main_file=None, last_world_file=None) for i in range(1, 26)
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|test.svg}}"
    mock_services["find_main_title"].return_value = "test.svg"

    # Track save_progress calls
    save_progress_calls: list = []
    original_save = mock_services["save_job_result_by_name"]

    def track_save(*args, **kwargs):
        save_progress_calls.append(args)
        return original_save(*args, **kwargs)

    mock_services["save_job_result_by_name"].side_effect = track_save

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Progress should be saved at: 1, 10, 20, and final
    # Expecting at least 3 saves (n=1, n=10, n=20, plus final)
    assert len(save_progress_calls) >= 3


def test_collect_templates_data_only_last_world_file(mock_services, monkeypatch: pytest.MonkeyPatch):
    """Test template with only last_world_file (no main_file)."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None, source=""),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates

    wikitext_without_main = """
    {{owidslidersrcs|id=gallery|widths=240|heights=240
    |gallery-World=
    File:test, World, 2021.svg!year=2021
    }}
    """

    mock_services["MwClientPage"].return_value.get_text.return_value = wikitext_without_main
    mock_services["find_main_title"].return_value = None  # No main file

    # Mock find_newest_world_file
    mock_find_last_world = MagicMock(return_value="test, World, 2021.svg")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_newest_world_file",
        mock_find_last_world,
    )

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should update template with only last_world_file
    mock_services["update_template_data"].assert_called_once_with(
        1,
        {
            "last_world_file": "test, World, 2021.svg",
            "last_world_year": 2021,
            "slug": "test",
        },
    )

    # Should save result as updated
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_updated"]) == 1


def test_collect_templates_data_template_with_existing_main_file_only(mock_services):
    """Test that templates with main_file but no last_world_file are processed."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="existing.svg", last_world_file=None, source=""),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|test.svg}}"
    mock_services["find_main_title"].return_value = "test.svg"

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should process template because last_world_file is missing
    mock_services["MwClientPage"].return_value.get_text.assert_called_once()

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1


def test_collect_templates_data_add_template_generic_exception(mock_services):
    """Test that generic exceptions during add_template are tracked in pages_failed."""
    existing_templates: list = []
    category_templates = ["Template:New1"]

    mock_services["get_category_members"].return_value = category_templates
    mock_services["list_templates"].return_value = existing_templates
    mock_services["add_template_data"].side_effect = RuntimeError("Database connection failed")

    runner.collect_templates_data_entry(job_id=1, user=None)

    # Should track in pages_failed but not increment summary["failed"] (that's for processing phase)
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_added"]) == 0
    assert len(result_dict["pages_failed"]) >= 1
    assert "Database connection failed" in result_dict["pages_failed"][0]["error"]


def test_collect_templates_data_update_all_processes_all_templates(mock_services, mock_find_source):
    """Test that update_all=True processes templates that already have all fields."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg", source="src1"
        ),
        TemplateRecord(
            id=2, title="Template:Test2", main_file="test2.svg", last_world_file="test2_2020.svg", source="src2"
        ),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
    mock_services["find_main_title"].return_value = "newfile.svg"

    # With update_all=True, both templates should be processed even though they have data
    runner.collect_templates_data_entry(job_id=1, user=None, args={"update_all": "true"})

    # Both templates should have had their wikitext fetched
    assert mock_services["MwClientPage"].return_value.get_text.call_count == 2


def test_collect_templates_data_default_skips_complete_templates(mock_services):
    """Test that without update_all, templates with all fields are skipped."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg", source="src1"
        ),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates

    # Without args (update_all=False by default), complete templates are skipped
    runner.collect_templates_data_entry(job_id=1, user=None)

    # No wikitext should be fetched for a complete template
    mock_services["MwClientPage"].return_value.get_text.assert_not_called()


def test_collect_templates_data_entry_with_update_all_true_string(mock_services, mock_find_source):
    """Test args parsing: args={'update_all': 'true'} enables update_all mode."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test1", main_file="existing.svg", last_world_file="world.svg", source="src"
        ),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
    mock_services["find_main_title"].return_value = "newfile.svg"

    runner.collect_templates_data_entry(job_id=1, user=None, args={"update_all": "true"})

    # Should process the template even though it already has data
    mock_services["MwClientPage"].return_value.get_text.assert_called_once()


def test_collect_templates_data_entry_with_update_all_false_string(mock_services):
    """Test args parsing: args={'update_all': 'false'} does not enable update_all mode."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test1", main_file="existing.svg", last_world_file="world.svg", source="src"
        ),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates

    runner.collect_templates_data_entry(job_id=1, user=None, args={"update_all": "false"})

    # Template is complete, should not be fetched
    mock_services["MwClientPage"].return_value.get_text.assert_not_called()


def test_collect_templates_data_entry_with_args_none(mock_services):
    """Test that args=None means update_all=False."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test1", main_file="existing.svg", last_world_file="world.svg", source="src"
        ),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates

    runner.collect_templates_data_entry(job_id=1, user=None, args=None)

    # Template is complete, should not be fetched
    mock_services["MwClientPage"].return_value.get_text.assert_not_called()


def test_collect_templates_data_entry_update_all_case_insensitive(mock_services, mock_find_source):
    """Test that update_all parsing is case-insensitive (e.g. 'TRUE', 'True')."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test1", main_file="existing.svg", last_world_file="world.svg", source="src"
        ),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
    mock_services["find_main_title"].return_value = "newfile.svg"

    runner.collect_templates_data_entry(job_id=1, user=None, args={"update_all": "TRUE"})

    # Should process even with uppercase "TRUE"
    mock_services["MwClientPage"].return_value.get_text.assert_called_once()


def test_collect_templates_data_entry_cancel_event_is_keyword_only(mock_services):
    """Test that cancel_event is keyword-only in collect_templates_data_entry."""
    import threading

    cancel_event = threading.Event()
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = []

    # Should not raise a TypeError - cancel_event must be passed as keyword arg
    runner.collect_templates_data_entry(job_id=1, user=None, cancel_event=cancel_event)

    # last call
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_collect_templates_data_entry_update_all_summary_counts(mock_services, mock_find_source):
    """Test that update_all mode processes all templates including those already complete."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg", source="src1"
        ),
        TemplateRecord(id=2, title="Template:Test2", main_file=None, last_world_file=None, source=""),
    ]
    mock_services["get_category_members"].return_value = []
    mock_services["list_templates"].return_value = templates
    mock_services["MwClientPage"].return_value.get_text.return_value = "{{SVGLanguages|newfile.svg}}"
    mock_services["find_main_title"].return_value = "newfile.svg"

    runner.collect_templates_data_entry(job_id=1, user=None, args={"update_all": "true"})

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    # Total is 2, 1 already had all data
    assert result_dict["summary"]["total"] == 2
    # With update_all, both templates are processed
    assert mock_services["MwClientPage"].return_value.get_text.call_count == 2
