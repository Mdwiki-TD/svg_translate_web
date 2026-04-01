"""Tests for the CopySvgLangsProcessor and its steps."""

from __future__ import annotations

from src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_text import extract_text_step
from src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles import extract_titles_step


def test_extract_text_step_success(mocker):
    mock_get_wikitext = mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_text.get_wikitext")
    mock_get_wikitext.return_value = "some wikitext"

    result = extract_text_step({}, "File:Example.svg")

    assert result[1]["status"] == "Completed"
    assert result[0] == "some wikitext"
    mock_get_wikitext.assert_called_once_with("File:Example.svg")


def test_extract_text_step_fail(mocker):
    mock_get_wikitext = mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_text.get_wikitext")
    mock_get_wikitext.return_value = ""

    result = extract_text_step({}, "File:Example.svg")

    assert result[1]["status"] == "Failed"
    assert result[0] == ""


def test_extract_titles_step_success(mocker):
    mock_get_files_list = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles.get_files_list"
    )
    mock_get_files_list.return_value = ("Main.svg", ["File1.svg", "File2.svg"])

    result = extract_titles_step({}, "some text", None)

    assert result[1]["status"] == "Completed"
    assert result[0]["main_title"] == "Main.svg"
    assert result[0]["titles"] == ["File1.svg", "File2.svg"]


def test_extract_titles_step_manual_title(mocker):
    mock_get_files_list = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles.get_files_list"
    )
    mock_get_files_list.return_value = ("Main.svg", ["File1.svg", "File2.svg"])

    result = extract_titles_step({}, "some text", "Manual.svg")

    assert result[1]["status"] == "Completed"
    assert result[0]["main_title"] == "Manual.svg"


def test_extract_titles_step_limit(mocker):
    mock_get_files_list = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.extract_titles.get_files_list"
    )
    mock_get_files_list.return_value = ("Main.svg", ["File1.svg", "File2.svg", "File3.svg"])

    result = extract_titles_step({}, "some text", None, titles_limit=2)

    assert result[1]["status"] == "Completed"
    assert len(result[0]["titles"]) == 2
    assert result[0]["titles"] == ["File1.svg", "File2.svg"]
