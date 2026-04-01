from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import pytest

from src.main_app.jobs_workers.copy_svg_langs.legacy_run_task import _compute_output_dir, fail_task, make_stages, run_task


@patch("src.main_app.jobs_workers.copy_svg_langs.legacy_run_task.settings")
def test_compute_output_dir(mock_settings, tmp_path):
    mock_settings.paths.svg_data = tmp_path

    # Simple title
    title = "Simple Title"
    out = _compute_output_dir(title)
    expected = tmp_path / "simple_title"
    assert out == expected
    assert out.exists()
    assert (out / "title.txt").read_text(encoding="utf-8") == "Simple Title"

    title3 = "Death Rate"
    out3 = _compute_output_dir(title3)
    assert out3.name == "death_rate"


def test_make_stages():
    stages = make_stages()
    assert "initialize" in stages
    assert "text" in stages
    assert "titles" in stages
    assert stages["initialize"]["status"] == "Running"
    assert stages["text"]["status"] == "Pending"


def test_fail_task():
    store = MagicMock()
    stages = make_stages()

    fail_task(store, "t1", stages, "Error msg")

    assert stages["initialize"]["status"] == "Completed"
    store.update_stage.assert_called_with("t1", "initialize", stages["initialize"])
    store.update_status.assert_called_with("t1", "Failed")


@patch("src.main_app.jobs_workers.copy_svg_langs.legacy_run_task.TaskStorePyMysql")
@patch("src.main_app.jobs_workers.copy_svg_langs.legacy_run_task.CopySvgLangsProcessor")
def test_run_task_success(
    mock_processor_cls,
    mock_store_cls,
):
    # Setup Mocks
    mock_store = mock_store_cls.return_value.__enter__.return_value
    mock_processor = mock_processor_cls.return_value

    # Mock successful run
    mock_processor.run.return_value = {
        "status": "completed",
        "stages": {
            "text": {"status": "Completed", "message": "Done"},
            "titles": {"status": "Completed", "message": "Done", "data": {"main_title": "Main.svg"}},
            "translations": {"status": "Completed"},
            "download": {"status": "Completed"},
            "nested": {"status": "Completed"},
            "inject": {"status": "Completed"},
            "upload": {"status": "Completed"},
        },
        "results_summary": {"total": 1}
    }
    mock_processor.result = mock_processor.run.return_value

    args = MagicMock()
    args.manual_main_title = None
    args.titles_limit = 5
    args.overwrite = False
    args.upload = False

    run_task({}, "t1", "Title", args, None)

    # Verification
    mock_store.update_status.assert_any_call("t1", "Running")
    mock_store.update_status.assert_any_call("t1", "Completed")
    mock_store.update_results.assert_called()


@patch("src.main_app.jobs_workers.copy_svg_langs.legacy_run_task.TaskStorePyMysql")
@patch("src.main_app.jobs_workers.copy_svg_langs.legacy_run_task.CopySvgLangsProcessor")
def test_run_task_fail_text(mock_processor_cls, mock_store_cls):
    mock_store = mock_store_cls.return_value.__enter__.return_value
    mock_processor = mock_processor_cls.return_value

    # Fail at text stage
    mock_processor.run.return_value = {
        "status": "failed",
        "stages": {
            "text": {"status": "Failed", "message": "Error"},
        }
    }
    mock_processor.result = mock_processor.run.return_value

    args = MagicMock()
    run_task({}, "t1", "Title", args, None)

    mock_store.update_status.assert_any_call("t1", "Failed")


@patch("src.main_app.jobs_workers.copy_svg_langs.legacy_run_task.TaskStorePyMysql")
@patch("src.main_app.jobs_workers.copy_svg_langs.legacy_run_task.CopySvgLangsProcessor")
def test_run_task_fail_titles(mock_processor_cls, mock_store_cls):
    mock_store = mock_store_cls.return_value.__enter__.return_value
    mock_processor = mock_processor_cls.return_value

    # Fail at titles stage
    mock_processor.run.return_value = {
        "status": "failed",
        "stages": {
            "text": {"status": "Completed"},
            "titles": {"status": "Failed", "message": "No titles"},
        }
    }
    mock_processor.result = mock_processor.run.return_value

    args = MagicMock()
    args.manual_main_title = None

    run_task({}, "t1", "Title", args, None)

    mock_store.update_status.assert_any_call("t1", "Failed")
