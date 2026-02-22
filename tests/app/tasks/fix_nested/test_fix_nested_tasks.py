import pytest
from unittest.mock import MagicMock, patch
from src.main_app.tasks.fix_nested.fix_nested_tasks import fix_nested_task

@patch("src.app.tasks.fix_nested.fix_nested_tasks.match_nested_tags")
@patch("src.app.tasks.fix_nested.fix_nested_tasks.fix_nested_file")
def test_fix_nested_task_success(mock_fix, mock_match):
    # Setup mocks
    # First call to match returns 1 tag, second call returns [] (fixed)
    mock_match.side_effect = [["tag1"], []]
    mock_fix.return_value = True

    stages = {}
    files = ["file1.svg"]

    data, final_stages = fix_nested_task(stages, files)

    assert data["status"]["fixed"] == 1
    assert data["status"]["len_nested_files"] == 1
    assert final_stages["status"] == "Completed"

@patch("src.app.tasks.fix_nested.fix_nested_tasks.match_nested_tags")
def test_fix_nested_task_no_nested(mock_match):
    mock_match.return_value = []

    stages = {}
    files = ["file1.svg"]

    data, final_stages = fix_nested_task(stages, files)

    assert data["status"]["len_nested_files"] == 0
    assert data["status"]["fixed"] == 0
    assert final_stages["status"] == "Completed"
