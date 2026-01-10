import pytest
from unittest.mock import patch
from src.app.tasks.titles.titles_tasks import titles_task

@patch("src.app.tasks.titles.titles_tasks.get_files_list")
def test_titles_task_success(mock_get_files):
    mock_get_files.return_value = ("Main.svg", ["f1.svg", "f2.svg"])
    stages = {}
    
    data, final_stages = titles_task(stages, "wikitext", None)
    
    assert data["main_title"] == "Main.svg"
    assert len(data["titles"]) == 2
    assert final_stages["status"] == "Completed"

@patch("src.app.tasks.titles.titles_tasks.get_files_list")
def test_titles_task_fail(mock_get_files):
    mock_get_files.return_value = (None, [])
    stages = {}
    
    data, final_stages = titles_task(stages, "wikitext", None)
    
    assert final_stages["status"] == "Failed"