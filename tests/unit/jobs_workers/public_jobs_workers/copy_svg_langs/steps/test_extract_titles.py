from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_titles import extract_titles_step


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    mocks = {
        "get_files_list_data": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data",
        mocks["get_files_list_data"],
    )
    return mocks


def test_titles_task_success(mock_services):
    mock_services["get_files_list_data"].return_value = {"main_title": "Main.svg", "titles": ["f1.svg", "f2.svg"]}

    data = extract_titles_step("wikitext")

    assert data["success"] is True
    assert data["main_title"] == "Main.svg"
    assert len(data["titles"]) == 2


def test_titles_task_manual_title(mock_services):
    mock_services["get_files_list_data"].return_value = {"main_title": "Main.svg", "titles": ["f1.svg"]}

    data = extract_titles_step("wikitext", manual_main_title="Manual.svg")

    assert data["main_title"] == "Manual.svg"


def test_titles_task_fail(mock_services):
    mock_services["get_files_list_data"].return_value = {"main_title": None, "titles": []}

    data = extract_titles_step("wikitext")

    assert data["success"] is False


def test_extract_titles_step_success(mock_services):
    mock_services["get_files_list_data"].return_value = {"main_title": "Main.svg", "titles": ["File1.svg", "File2.svg"]}

    result = extract_titles_step("some text")

    assert result["success"] is True
    assert result["main_title"] == "Main.svg"
    assert result["titles"] == ["File1.svg", "File2.svg"]
    assert result["error"] is None


def test_extract_titles_step_manual_title(mock_services):
    mock_services["get_files_list_data"].return_value = {"main_title": "Main.svg", "titles": ["File1.svg", "File2.svg"]}

    result = extract_titles_step("some text", manual_main_title="Manual.svg")

    assert result["success"] is True
    assert result["main_title"] == "Manual.svg"
