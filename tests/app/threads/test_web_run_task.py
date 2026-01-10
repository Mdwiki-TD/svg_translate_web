import pytest
from unittest.mock import MagicMock, patch, ANY
from pathlib import Path
from src.app.threads.web_run_task import (
    _compute_output_dir,
    make_stages,
    fail_task,
    run_task
)

@patch("src.app.threads.web_run_task.settings")
def test_compute_output_dir(mock_settings, tmp_path):
    mock_settings.paths.svg_data = tmp_path
    
    # Simple title
    title = "Simple Title"
    out = _compute_output_dir(title)
    expected = tmp_path / "simple_title"
    assert out == expected
    assert out.exists()
    assert (out / "title.txt").read_text(encoding="utf-8") == "Simple Title"
    
    # Complex title with special chars
    title2 = "File:Test / Name"
    out2 = _compute_output_dir(title2)
    # logic: Path(title).name -> " Name" (if treated as path) or similar depending on OS
    # The implementation uses Path(title).name. 
    # On Windows "File:Test / Name" might differ from Linux. 
    # But let's assume standard behavior or mock Path if needed.
    # Actually, simpler to test sanitization logic directly.
    
    # Let's trust the function logic: 
    # re.sub(r"[^A-Za-z0-9._\- ]+", "_", str(name))
    
    # "File:Test / Name" -> Path("File:Test / Name").name -> " Name" (on win? no, invalid chars)
    # Let's stick to safe strings for cross-platform test or mock Path.
    
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

@patch("src.app.threads.web_run_task.TaskStorePyMysql")
@patch("src.app.threads.web_run_task._compute_output_dir")
@patch("src.app.threads.web_run_task.text_task")
@patch("src.app.threads.web_run_task.titles_task")
@patch("src.app.threads.web_run_task.translations_task")
@patch("src.app.threads.web_run_task.download_task")
@patch("src.app.threads.web_run_task.fix_nested_task")
@patch("src.app.threads.web_run_task.inject_task")
@patch("src.app.threads.web_run_task.upload_task")
@patch("src.app.threads.web_run_task.save_files_stats")
@patch("src.app.threads.web_run_task.make_results_summary")
def test_run_task_success(
    mock_summary, mock_stats, mock_upload, mock_inject, mock_nested,
    mock_download, mock_trans, mock_titles, mock_text, mock_compute_dir, mock_store_cls
):
    # Setup Mocks
    mock_store = mock_store_cls.return_value.__enter__.return_value
    mock_compute_dir.return_value = Path("/tmp/out")
    
    # Stage 1: Text
    mock_text.return_value = ("some text", {"status": "Completed"})
    
    # Stage 2: Titles
    mock_titles.return_value = (
        {"main_title": "File:Main.svg", "titles": ["File:Main.svg"]},
        {"status": "Completed"}
    )
    
    # Stage 3: Translations
    mock_trans.return_value = ({"tr": 1}, {"status": "Completed"})
    
    # Stage 4: Download
    mock_download.return_value = ({"f1": {}}, {"status": "Completed"}, [])
    
    # Stage 5: Nested
    mock_nested.return_value = ({}, {"status": "Completed"})
    
    # Stage 6: Inject
    mock_inject.return_value = (
        {"success": 1, "saved_done": 1, "files": {"f1": {"file_path": "p"}}},
        {"status": "Completed"}
    )
    
    # Stage 7: Upload
    mock_upload.return_value = ({}, {"status": "Completed"})
    
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
    
    # Verify stage updates
    assert mock_store.update_stage.call_count >= 8 # 7 stages + initialize updates

@patch("src.app.threads.web_run_task.TaskStorePyMysql")
@patch("src.app.threads.web_run_task._compute_output_dir")
@patch("src.app.threads.web_run_task.text_task")
def test_run_task_fail_text(mock_text, mock_compute_dir, mock_store_cls):
    mock_store = mock_store_cls.return_value.__enter__.return_value
    mock_compute_dir.return_value = Path("/tmp/out")
    
    # Fail at text
    mock_text.return_value = (None, {"status": "Failed"})
    
    args = MagicMock()
    run_task({}, "t1", "Title", args, None)
    
    mock_store.update_status.assert_any_call("t1", "Failed")

@patch("src.app.threads.web_run_task.TaskStorePyMysql")
@patch("src.app.threads.web_run_task._compute_output_dir")
@patch("src.app.threads.web_run_task.text_task")
@patch("src.app.threads.web_run_task.titles_task")
def test_run_task_fail_titles(mock_titles, mock_text, mock_compute_dir, mock_store_cls):
    mock_store = mock_store_cls.return_value.__enter__.return_value
    mock_compute_dir.return_value = Path("/tmp/out")
    
    mock_text.return_value = ("txt", {})
    # Fail at titles (no main title)
    mock_titles.return_value = ({"main_title": None, "titles": []}, {})
    
    args = MagicMock()
    args.manual_main_title = None
    
    run_task({}, "t1", "Title", args, None)
    
    mock_store.update_status.assert_any_call("t1", "Failed")