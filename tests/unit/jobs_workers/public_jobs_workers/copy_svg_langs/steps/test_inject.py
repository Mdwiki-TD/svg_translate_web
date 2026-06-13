from unittest.mock import patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject import inject_step


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject.start_injects_wrap")
def test_inject_task_success(mock_start, tmp_path):
    mock_start.return_value = {"success": 2, "failed": 0, "no_changes": 1, "nested_files": 0, "files": {}}
    files = {"f1.svg": str(tmp_path / "f1.svg"), "f2.svg": str(tmp_path / "f2.svg")}
    translations: dict = {}

    res = inject_step(files, translations, output_dir=tmp_path)

    assert res["success"] is True
    assert res["summary"]["success"] == 2
    assert (tmp_path / "translated").exists()


def test_inject_task_no_dir():
    with pytest.raises(TypeError):
        inject_step([], {}, output_dir=None)


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject.start_injects_wrap")
def test_inject_step_exception(mock_start, tmp_path):
    mock_start.side_effect = RuntimeError("Injection crashed")

    files = {"f1.svg": str(tmp_path / "f1.svg")}
    res = inject_step(files, {}, output_dir=tmp_path)

    assert res["success"] is False
    assert res["summary"]["failed"] == 1
    assert "Injection failed" in res["message"]


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject.start_injects_wrap")
def test_inject_step_file_with_path(mock_start, tmp_path):
    mock_start.return_value = {
        "success": 1,
        "failed": 0,
        "no_changes": 0,
        "nested_files": 0,
        "files": {
            "f1.svg": {
                "file_path": "/out/translated/f1.svg",
                "new_languages": 3,
                "no_changes": "",
                "error": "",
            }
        },
    }

    files = {"f1.svg": str(tmp_path / "f1.svg")}
    res = inject_step(files, {}, output_dir=tmp_path)

    assert res["success"] is True
    assert res["results"]["f1.svg"]["result"] is True
    assert res["results"]["f1.svg"]["new_languages"] == 3


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject.start_injects_wrap")
def test_inject_step_title_in_files_no_changes(mock_start, tmp_path):
    mock_start.return_value = {
        "success": 0,
        "failed": 0,
        "no_changes": 1,
        "nested_files": 0,
        "files": {
            "f1.svg": {
                "file_path": "",
                "new_languages": "",
                "no_changes": True,
                "error": "",
            }
        },
    }

    files = {"f1.svg": str(tmp_path / "f1.svg")}
    res = inject_step(files, {}, output_dir=tmp_path)

    assert res["results"]["f1.svg"]["result"] is True
    assert res["results"]["f1.svg"]["new_languages"] == 0


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject.start_injects_wrap")
def test_inject_step_title_in_files_with_error(mock_start, tmp_path):
    mock_start.return_value = {
        "success": 0,
        "failed": 1,
        "no_changes": 0,
        "nested_files": 0,
        "files": {
            "f1.svg": {
                "file_path": "",
                "new_languages": "",
                "no_changes": False,
                "error": "Something went wrong",
            }
        },
    }

    files = {"f1.svg": str(tmp_path / "f1.svg")}
    res = inject_step(files, {}, output_dir=tmp_path)

    assert res["results"]["f1.svg"]["result"] is False
    assert "Something went wrong" in res["results"]["f1.svg"]["msg"]


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject.start_injects_wrap")
def test_inject_step_title_not_in_files(mock_start, tmp_path):
    mock_start.return_value = {
        "success": 0,
        "failed": 0,
        "no_changes": 0,
        "nested_files": 0,
        "files": {},
    }

    files = {"f1.svg": str(tmp_path / "f1.svg")}
    res = inject_step(files, {}, output_dir=tmp_path)

    assert res["results"]["f1.svg"]["result"] is False
    assert "failed or skipped" in res["results"]["f1.svg"]["msg"]


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject.start_injects_wrap")
def test_inject_step_empty_files(mock_start, tmp_path):
    mock_start.return_value = {
        "success": 0,
        "failed": 0,
        "no_changes": 0,
        "nested_files": 0,
        "files": {},
    }

    res = inject_step({}, {}, output_dir=tmp_path)

    assert res["success"] is True
    assert res["summary"]["total"] == 0
