from unittest.mock import patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles import extract_titles_step


@patch("src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles.get_files_list")
def test_titles_task_success(mock_get_files):
    mock_get_files.return_value = ("Main.svg", ["f1.svg", "f2.svg"])
    stages = {}

    data = extract_titles_step("wikitext")

    assert data["success"] is True
    assert data["main_title"] == "Main.svg"
    assert len(data["titles"]) == 2


@patch("src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles.get_files_list")
def test_titles_task_manual_title(mock_get_files):
    mock_get_files.return_value = ("Main.svg", ["f1.svg"])
    stages = {}

    data = extract_titles_step("wikitext", manual_main_title="Manual.svg")

    assert data["main_title"] == "Manual.svg"


@patch("src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles.get_files_list")
def test_titles_task_limit(mock_get_files):
    mock_get_files.return_value = ("Main.svg", ["f1.svg", "f2.svg", "f3.svg"])
    stages = {}

    data = extract_titles_step("wikitext", titles_limit=2)

    assert len(data["titles"]) == 2


@patch("src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles.get_files_list")
def test_titles_task_fail(mock_get_files):
    mock_get_files.return_value = (None, [])
    stages = {}

    data = extract_titles_step("wikitext")

    assert data["success"] is False
