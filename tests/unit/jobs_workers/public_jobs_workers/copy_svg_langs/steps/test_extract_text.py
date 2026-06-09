import pytest
from unittest.mock import MagicMock

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_text import extract_text_step


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    mock_get_page_text = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_text.get_page_text",
        mock_get_page_text,
    )
    return {"get_page_text": mock_get_page_text}


def test_text_task_success(mock_services):
    mock_services["get_page_text"].return_value = "content"

    result = extract_text_step("Title")

    assert result["success"] is True
    assert result["text"] == "content"


def test_text_task_fail(mock_services):
    mock_services["get_page_text"].return_value = None

    result = extract_text_step("Title")

    assert result["success"] is False
    assert result["text"] == ""


def test_extract_text_step_success(mock_services):
    mock_services["get_page_text"].return_value = "some wikitext"

    result = extract_text_step("File:Example.svg")

    assert result["success"] is True
    assert result["text"] == "some wikitext"
    assert result["error"] is None
    mock_services["get_page_text"].assert_called_once_with("File:Example.svg", None)


def test_extract_text_step_fail(mock_services):
    mock_services["get_page_text"].return_value = ""

    result = extract_text_step("File:Example.svg")

    assert result["success"] is False
    assert result["text"] == ""
    assert result["error"] == "No wikitext found"
