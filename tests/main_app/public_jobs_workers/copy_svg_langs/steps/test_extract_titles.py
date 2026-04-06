from unittest.mock import patch

from src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles import extract_titles_step


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data")
def test_titles_task_success(mock_get_files):
    mock_get_files.return_value = {"main_title": "Main.svg", "titles": ["f1.svg", "f2.svg"]}

    data = extract_titles_step("wikitext")

    assert data["success"] is True
    assert data["main_title"] == "Main.svg"
    assert len(data["titles"]) == 2


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data")
def test_titles_task_manual_title(mock_get_files):
    mock_get_files.return_value = {"main_title": "Main.svg", "titles": ["f1.svg"]}

    data = extract_titles_step("wikitext", manual_main_title="Manual.svg")

    assert data["main_title"] == "Manual.svg"


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data")
def test_titles_task_limit(mock_get_files):
    mock_get_files.return_value = {"main_title": "Main.svg", "titles": ["f1.svg", "f2.svg", "f3.svg"]}

    data = extract_titles_step("wikitext", titles_limit=2)

    assert len(data["titles"]) == 2


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data")
def test_titles_task_fail(mock_get_files):
    mock_get_files.return_value = {"main_title": None, "titles": []}

    data = extract_titles_step("wikitext")

    assert data["success"] is False


def test_extract_titles_step_success(mocker):
    mock_get_files_list_data = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data"
    )
    mock_get_files_list_data.return_value = {"main_title": "Main.svg", "titles": ["File1.svg", "File2.svg"]}

    result = extract_titles_step("some text")

    assert result["success"] is True
    assert result["main_title"] == "Main.svg"
    assert result["titles"] == ["File1.svg", "File2.svg"]
    assert result["error"] is None


def test_extract_titles_step_manual_title(mocker):
    mock_get_files_list_data = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data"
    )
    mock_get_files_list_data.return_value = {"main_title": "Main.svg", "titles": ["File1.svg", "File2.svg"]}

    result = extract_titles_step("some text", manual_main_title="Manual.svg")

    assert result["success"] is True
    assert result["main_title"] == "Manual.svg"


def test_extract_titles_step_limit(mocker):
    mock_get_files_list_data = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list_data"
    )
    mock_get_files_list_data.return_value = {
        "main_title": "Main.svg",
        "titles": ["File1.svg", "File2.svg", "File3.svg"],
    }

    result = extract_titles_step("some text", titles_limit=2)

    assert result["success"] is True
    assert len(result["titles"]) == 2
    assert result["titles"] == ["File1.svg", "File2.svg"]
