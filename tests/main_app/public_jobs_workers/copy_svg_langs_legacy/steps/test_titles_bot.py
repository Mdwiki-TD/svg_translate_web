from unittest.mock import patch

from src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles import extract_titles_step


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data")
def test_titles_task_success(mock_get_files):
    mock_get_files.return_value = {"main_title": "Main.svg", "titles": ["f1.svg", "f2.svg"]}
    stages = {}

    data = extract_titles_step("wikitext")

    assert data["success"] is True
    assert data["main_title"] == "Main.svg"
    assert len(data["titles"]) == 2


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data")
def test_titles_task_fail(mock_get_files):
    mock_get_files.return_value = {"main_title": None, "titles": []}
    stages = {}

    data = extract_titles_step("wikitext")

    assert data["success"] is False
