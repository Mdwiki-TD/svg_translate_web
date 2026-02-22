import pytest
from unittest.mock import patch
from src.main_app.tasks.titles.titles_tasks import titles_task

@patch("src.app.tasks.titles.titles_tasks.get_files_list")
def test_titles_task_success(mock_get_files):
    mock_get_files.return_value = ("Main.svg", ["f1.svg", "f2.svg"])
    stages = {}

    data, final_stages = titles_task(stages, "wikitext", None)

    assert data["main_title"] == "Main.svg"
    assert len(data["titles"]) == 2
    assert final_stages["status"] == "Completed"

@patch("src.app.tasks.titles.titles_tasks.get_files_list")
def test_titles_task_manual_title(mock_get_files):
    mock_get_files.return_value = ("Main.svg", ["f1.svg"])
    stages = {}

    data, final_stages = titles_task(stages, "wikitext", "Manual.svg")

    assert data["main_title"] == "Manual.svg"

@patch("src.app.tasks.titles.titles_tasks.get_files_list")
def test_titles_task_limit(mock_get_files):
    mock_get_files.return_value = ("Main.svg", ["f1.svg", "f2.svg", "f3.svg"])
    stages = {}

    data, final_stages = titles_task(stages, "wikitext", None, titles_limit=2)

    assert len(data["titles"]) == 2
    assert "use only 2" in final_stages["message"]

@patch("src.app.tasks.titles.titles_tasks.get_files_list")
def test_titles_task_fail(mock_get_files):
    mock_get_files.return_value = (None, [])
    stages = {}

    data, final_stages = titles_task(stages, "wikitext", None)

    assert final_stages["status"] == "Failed"
