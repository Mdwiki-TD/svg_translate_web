"""Tests for the CopySvgLangsProcessor and its steps."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.job import CopySvgLangsProcessor
from src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_text import extract_text_step
from src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles import extract_titles_step


def test_extract_text_step_success(mocker):
    mock_get_wikitext = mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_text.get_wikitext")
    mock_get_wikitext.return_value = "some wikitext"

    result = extract_text_step("File:Example.svg")

    assert result["success"] is True
    assert result["text"] == "some wikitext"
    assert result["error"] is None
    mock_get_wikitext.assert_called_once_with("File:Example.svg")


def test_extract_text_step_fail(mocker):
    mock_get_wikitext = mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_text.get_wikitext")
    mock_get_wikitext.return_value = ""

    result = extract_text_step("File:Example.svg")

    assert result["success"] is False
    assert result["text"] == ""
    assert result["error"] == "No wikitext found"


def test_extract_titles_step_success(mocker):
    mock_get_files_list = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list"
    )
    mock_get_files_list.return_value = ("Main.svg", ["File1.svg", "File2.svg"])

    result = extract_titles_step("some text")

    assert result["success"] is True
    assert result["main_title"] == "Main.svg"
    assert result["titles"] == ["File1.svg", "File2.svg"]
    assert result["error"] is None


def test_extract_titles_step_manual_title(mocker):
    mock_get_files_list = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list"
    )
    mock_get_files_list.return_value = ("Main.svg", ["File1.svg", "File2.svg"])

    result = extract_titles_step("some text", manual_main_title="Manual.svg")

    assert result["success"] is True
    assert result["main_title"] == "Manual.svg"


def test_extract_titles_step_limit(mocker):
    mock_get_files_list = mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_titles.get_files_list"
    )
    mock_get_files_list.return_value = ("Main.svg", ["File1.svg", "File2.svg", "File3.svg"])

    result = extract_titles_step("some text", titles_limit=2)

    assert result["success"] is True
    assert len(result["titles"]) == 2
    assert result["titles"] == ["File1.svg", "File2.svg"]


@pytest.fixture
def processor_args():
    args = MagicMock()
    # It's a dict in job.py, accessed with .get()
    return {
        "manual_main_title": None,
        "titles_limit": None,
        "overwrite": False,
        "upload": False
    }


@pytest.fixture
def initial_result():
    return {
        "status": "pending",
        "stages": {
            "text": {"status": "Pending", "number": 1},
            "titles": {"status": "Pending", "number": 2},
            "translations": {"status": "Pending", "number": 3},
            "download": {"status": "Pending", "number": 4},
            "nested": {"status": "Pending", "number": 5},
            "inject": {"status": "Pending", "number": 6},
            "upload": {"status": "Pending", "number": 7},
        },
        "files_processed": []
    }


def test_processor_compute_output_dir(processor_args, initial_result, mocker):
    mock_settings = mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.settings")
    mock_settings.paths.svg_data = "/tmp/svg_data"
    processor = CopySvgLangsProcessor(
        task_id=1,
        title="File:Test Path/Example.svg",
        args=processor_args,
        user=None,
        result=initial_result,
        result_file="job_1.json",
    )

    assert "example_svg" in str(processor.output_dir) or "example.svg" in str(processor.output_dir)


@patch("src.main_app.public_jobs_workers.copy_svg_langs.job.jobs_service")
def test_processor_run_text_stage_fail(mock_jobs_service, processor_args, initial_result, mocker):
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.settings")
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.create_commons_session")
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.get_user_site")
    mock_jobs_service.is_job_cancelled.return_value = False

    mock_extract_text = mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.extract_text_step")
    mock_extract_text.return_value = {"success": False, "error": "Failed to get text"}

    processor = CopySvgLangsProcessor(
        task_id=1,
        title="Test",
        args=processor_args,
        user=None,
        result=initial_result,
        result_file="job_1.json",
    )

    result = processor.run()

    assert result["status"] == "failed"
    assert result["stages"]["text"]["status"] == "Failed"
    assert result["stages"]["text"]["message"] == "Failed to get text"


@patch("src.main_app.public_jobs_workers.copy_svg_langs.job.jobs_service")
def test_processor_files_processed_tracking(mock_jobs_service, processor_args, initial_result, mocker, tmp_path):
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.settings")
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.create_commons_session")
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.get_user_site")
    mock_jobs_service.is_job_cancelled.return_value = False

    # Mock stages
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.extract_text_step", return_value={"success": True, "text": "wikitext"})
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.extract_titles_step", return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]})
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.extract_translations_step", return_value={"success": True, "translations": {"new": {}}})

    # Mock download step with results
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.download_step", return_value={
        "success": True,
        "files": [str(tmp_path / "files" / "File1.svg")],
        "results": {"File1.svg": {"result": True, "msg": "Downloaded"}},
        "summary": {}
    })

    # Mock nested step
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.fix_nested_step", return_value={
        "success": True,
        "data": {},
        "results": {str(tmp_path / "files" / "File1.svg"): {"result": True, "msg": "Fixed"}},
        "summary": {}
    })

    # Mock inject step
    mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.inject_step", return_value={
        "success": True,
        "data": {},
        "files_to_upload": {"File1.svg": {"file_path": str(tmp_path / "translated" / "File1.svg"), "new_languages": 1}},
        "results": {str(tmp_path / "files" / "File1.svg"): {"result": True, "msg": "Injected"}},
        "summary": {}
    })

    # Mock upload disabled
    processor_args["upload"] = False

    processor = CopySvgLangsProcessor(
        task_id=1,
        title="Test",
        args=processor_args,
        user=None,
        result=initial_result,
        result_file="job_1.json",
    )

    # Override output_dir to have a predictable path for matching
    processor.output_dir = tmp_path

    result = processor.run()

    assert len(result["files_processed"]) == 1
    file_info = result["files_processed"][0]
    assert file_info["title"] == "File1.svg"
    assert file_info["steps"]["download"]["result"] is True
    assert file_info["steps"]["nested"]["result"] is True
    assert file_info["steps"]["inject"]["result"] is True
    assert file_info["steps"]["upload"]["result"] is None # Upload disabled
    assert file_info["status"] == "completed"
