from unittest.mock import patch

from src.main_app.public_jobs.workers.copy_svg_langs.steps.extract_text import extract_text_step


@patch("src.main_app.public_jobs.workers.copy_svg_langs.steps.extract_text.get_page_text")
def test_text_task_success(mock_get):
    mock_get.return_value = "content"

    result = extract_text_step("Title")

    assert result["success"] is True
    assert result["text"] == "content"


@patch("src.main_app.public_jobs.workers.copy_svg_langs.steps.extract_text.get_page_text")
def test_text_task_fail(mock_get):
    mock_get.return_value = None

    result = extract_text_step("Title")

    assert result["success"] is False
    assert result["text"] == ""


def test_extract_text_step_success(mocker):
    mock_get_page_text = mocker.patch(
        "src.main_app.public_jobs.workers.copy_svg_langs.steps.extract_text.get_page_text"
    )
    mock_get_page_text.return_value = "some wikitext"

    result = extract_text_step("File:Example.svg")

    assert result["success"] is True
    assert result["text"] == "some wikitext"
    assert result["error"] is None
    mock_get_page_text.assert_called_once_with("File:Example.svg", None)


def test_extract_text_step_fail(mocker):
    mock_get_page_text = mocker.patch(
        "src.main_app.public_jobs.workers.copy_svg_langs.steps.extract_text.get_page_text"
    )
    mock_get_page_text.return_value = ""

    result = extract_text_step("File:Example.svg")

    assert result["success"] is False
    assert result["text"] == ""
    assert result["error"] == "No wikitext found"
