"""Tests for the CopySvgLangsProcessor and its steps."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.job import CopySvgLangsProcessor


@pytest.fixture
def processor_args():
    _args = MagicMock()
    # It's a dict in job.py, accessed with .get()
    return {"manual_main_title": None, "titles_limit": None, "overwrite": False, "upload": False}


@pytest.fixture
def initial_result():
    return {
        "status": "pending",
        "stages": {
            "text": {"status": "Pending"},
            "titles": {"status": "Pending"},
            "translations": {"status": "Pending"},
            "download": {"status": "Pending"},
            "nested": {"status": "Pending"},
            "inject": {"status": "Pending"},
            "upload": {"status": "Pending"},
        },
        "files_processed": {},
        "results_summary": {},
    }


def test_processor_compute_output_dir(processor_args, initial_result, mocker):
    mock_settings = mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.settings")
    mock_settings.paths.svg_data = "/tmp/svg_data"
    processor_args_with_title = {**processor_args, "title": "File:Test Path/Example.svg"}
    processor = CopySvgLangsProcessor(
        task_id=1,
        args=processor_args_with_title,
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

    processor_args_with_title = {**processor_args, "title": "Test"}
    processor = CopySvgLangsProcessor(
        task_id=1,
        args=processor_args_with_title,
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
    mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.job.extract_text_step",
        return_value={"success": True, "text": "wikitext"},
    )
    mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.job.extract_titles_step",
        return_value={"success": True, "main_title": "Main.svg", "titles": ["File1.svg"], "message": "Found 1 titles"},
    )
    mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.job.extract_translations_step",
        return_value={"success": True, "translations": {"new": {}}, "message": "Extracted translations"},
    )

    # Mock download step with results - use side_effect to call progress_callback
    def download_side_effect(*args, **kwargs):
        results = {"File1.svg": {"result": True, "msg": "Downloaded"}}
        if kwargs.get("progress_callback"):
            kwargs["progress_callback"](1, 1, "Downloaded", results)
        return {
            "success": True,
            "files": [str(tmp_path / "files" / "File1.svg")],
            "files_dict": {"File1.svg": str(tmp_path / "files" / "File1.svg")},
            "summary": {"downloaded": 1, "skipped_existing": 0, "failed": 0},
        }

    mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.job.download_step",
        side_effect=download_side_effect,
    )

    # Mock nested step - use side_effect to call progress_callback
    def nested_side_effect(*args, **kwargs):
        results = {"File1.svg": {"result": True, "msg": "Fixed"}}
        if kwargs.get("progress_callback"):
            kwargs["progress_callback"](1, 1, "Fixed", results)
        return {
            "success": True,
            "data": {"data": {}, "results": {}},
            "summary": {},
        }

    mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.job.fix_nested_step",
        side_effect=nested_side_effect,
    )

    # Mock inject step
    mocker.patch(
        "src.main_app.public_jobs_workers.copy_svg_langs.job.inject_step",
        return_value={
            "success": True,
            "data": {
                "files": {"File1.svg": {"file_path": str(tmp_path / "translated" / "File1.svg"), "new_languages": 1}}
            },
            "files_to_upload": {
                "File1.svg": {"file_path": str(tmp_path / "translated" / "File1.svg"), "new_languages": 1}
            },
            "results": {"File1.svg": {"result": True, "msg": "Injected 1 languages"}},
            "summary": {},
        },
    )

    # Mock upload disabled
    processor_args_with_title = {**processor_args, "upload": False, "title": "Test"}

    processor = CopySvgLangsProcessor(
        task_id=1,
        args=processor_args_with_title,
        user=None,
        result=initial_result,
        result_file="job_1.json",
    )

    # Override output_dir to have a predictable path for matching
    processor.output_dir = tmp_path

    result = processor.run()

    assert len(result["files_processed"]) == 1
    file_info = result["files_processed"]["File1.svg"]
    assert file_info["title"] == "File1.svg"
    assert file_info["steps"]["download"]["result"] is True
    assert file_info["steps"]["nested"]["result"] is True
    assert file_info["steps"]["inject"]["result"] is True
    assert file_info["steps"]["upload"]["result"] is None  # Upload disabled
    assert file_info["status"] == "Skipped"
