import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.main_app.tasks.injects.inject_tasks import inject_task

@patch("src.app.tasks.injects.inject_tasks.start_injects")
def test_inject_task_success(mock_start, tmp_path):
    mock_start.return_value = {
        "success": 2,
        "failed": 0,
        "no_changes": 1,
        "nested_files": 0
    }
    stages = {}
    files = ["f1.svg", "f2.svg"]
    translations = {}

    res, final_stages = inject_task(stages, files, translations, output_dir=tmp_path)

    assert res["success"] == 2
    assert final_stages["status"] == "Completed"
    assert (tmp_path / "translated").exists()

def test_inject_task_no_dir():
    stages = {}
    res, final_stages = inject_task(stages, [], {}, output_dir=None)
    assert final_stages["status"] == "Failed"
    assert res == {}
