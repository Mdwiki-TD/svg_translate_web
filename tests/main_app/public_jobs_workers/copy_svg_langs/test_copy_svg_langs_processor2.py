"""Tests for the CopySvgLangsProcessor and its steps."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.job import CopySvgLangsProcessor


@pytest.fixture
def processor_args():
    args = MagicMock()
    args.manual_main_title = None
    args.titles_limit = None
    args.overwrite = False
    args.upload = False
    return args


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
    }


def test_processor_compute_output_dir(processor_args, initial_result, mocker):
    mock_settings = mocker.patch("src.main_app.public_jobs_workers.copy_svg_langs.job.settings")
    mock_settings.paths.svg_data = "/tmp/svg_data"
    processor = CopySvgLangsProcessor(
        job_id=1,
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
        job_id=1,
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
