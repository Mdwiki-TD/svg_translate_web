from unittest.mock import MagicMock

import pytest
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps import ExtractSteps


@pytest.fixture
def mock_extract_text_services(monkeypatch: pytest.MonkeyPatch):
    mocks = {
        "MwClientPage": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.MwClientPage",
        mocks["MwClientPage"],
    )
    return mocks


def test_text_task_success(mock_extract_text_services):
    mock_extract_text_services["MwClientPage"].return_value.get_text.return_value = "content"

    result = ExtractSteps.extract_text_step("Title")

    assert result.success is True
    assert result.text == "content"


def test_text_task_fail(mock_extract_text_services):
    mock_extract_text_services["MwClientPage"].return_value.get_text.return_value = None

    result = ExtractSteps.extract_text_step("Title")

    assert result.success is False
    assert result.text == ""


def test_extract_text_step_success(mock_extract_text_services):
    mock_extract_text_services["MwClientPage"].return_value.get_text.return_value = "some wikitext"

    result = ExtractSteps.extract_text_step("File:Example.svg")

    assert result.success is True
    assert result.text == "some wikitext"
    assert result.error is None
    mock_extract_text_services["MwClientPage"].assert_called_once_with("File:Example.svg", None)


def test_extract_text_step_fail(mock_extract_text_services):
    mock_extract_text_services["MwClientPage"].return_value.get_text.return_value = ""

    result = ExtractSteps.extract_text_step("File:Example.svg")

    assert result.success is False
    assert result.text == ""
    assert result.error == "No wikitext found"


def test_extract_text_step_empty_title():
    result = ExtractSteps.extract_text_step("")

    assert result.success is False
    assert result.text == ""
    assert result.error == "No title found"


def test_extract_text_step_none_title():
    result = ExtractSteps.extract_text_step(None)  # pyright: ignore[reportArgumentType]

    assert result.success is False
    assert result.text == ""
    assert result.error == "No title found"
