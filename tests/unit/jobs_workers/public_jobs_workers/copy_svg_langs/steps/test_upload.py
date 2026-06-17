from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload import upload_step


@pytest.fixture
def mock_store():
    return MagicMock()


def test_upload_task_disabled(mock_site):
    res = upload_step({}, "Main", site=mock_site)
    assert res["success"] is True
    assert res["summary"]["total"] == 0


def test_upload_task_no_files(mock_site):
    res = upload_step({}, "Main", site=mock_site)
    assert res["success"] is True
    assert res["summary"]["total"] == 0


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_task_success(mock_upload, mock_site):
    mock_upload.return_value = {"result": "success"}

    files = {"f1": {"file_path": "/path/to/f1.svg", "new_languages": 1}}

    res = upload_step(files, "Main", site=mock_site)

    assert res["summary"]["uploaded"] == 1
    mock_upload.assert_called_once()


def test_upload_no_new_languages(mock_site):
    files = {"f1": {"file_path": "/path/to/f1.svg", "new_languages": 0}}

    res = upload_step(files, "Main", site=mock_site)

    assert res["success"] is True
    assert res["summary"]["no_changes"] == 1
    assert res["results"]["f1"]["result"] is None
    assert "No new languages" in res["results"]["f1"]["msg"]


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_cancelled(mock_upload, mock_site):
    mock_upload.return_value = {"result": "success"}
    files = {
        "f1": {"file_path": "/p1", "new_languages": 1},
        "f2": {"file_path": "/p2", "new_languages": 1},
    }

    _res = upload_step(files, "Main", site=mock_site, cancel_check=lambda: True)

    assert mock_upload.call_count == 0


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_limit(mock_upload, mock_site):
    mock_upload.return_value = {"result": "success"}
    files = {
        "f1": {"file_path": "/p1", "new_languages": 1},
        "f2": {"file_path": "/p2", "new_languages": 1},
        "f3": {"file_path": "/p3", "new_languages": 1},
    }

    res = upload_step(files, "Main", site=mock_site, upload_limit=1)

    assert mock_upload.call_count == 1
    assert res["results"]["f2"]["msg"] == "Reached upload limit"
    assert res["results"]["f3"]["msg"] == "Reached upload limit"


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_fileexists_no_change(mock_upload, mock_site):
    mock_upload.return_value = {"result": "fileexists-no-change"}
    files = {"f1": {"file_path": "/p1", "new_languages": 1}}

    res = upload_step(files, "Main", site=mock_site)

    assert res["summary"]["no_changes"] == 1
    assert res["results"]["f1"]["result"] is True
    assert "already exists" in res["results"]["f1"]["msg"]


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_error(mock_upload, mock_site):
    mock_upload.return_value = {"result": "Error", "error": "Permission denied"}
    files = {"f1": {"file_path": "/p1", "file_name": "f1.svg", "new_languages": 1}}

    res = upload_step(files, "Main", site=mock_site)

    assert res["summary"]["failed"] == 1
    assert res["results"]["f1"]["result"] is False
    assert len(res["errors"]) == 1


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_exception(mock_upload, mock_site):
    mock_upload.side_effect = ConnectionError("Network down")
    files = {"f1": {"file_path": "/p1", "file_name": "f1.svg", "new_languages": 1}}

    res = upload_step(files, "Main", site=mock_site)

    assert res["summary"]["failed"] == 1
    assert res["results"]["f1"]["result"] is False
    assert "Network down" in res["results"]["f1"]["msg"]
    assert len(res["errors"]) == 1


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_progress_callback(mock_upload, mock_site):
    mock_upload.return_value = {"result": "success"}
    progress_calls = []

    def progress_cb(index):
        progress_calls.append({"index": index})

    files = {f"f{i}": {"file_path": f"/p{i}", "new_languages": 1} for i in range(15)}

    upload_step(files, "Main", site=mock_site, progress_callback=progress_cb)

    assert len(progress_calls) >= 1


def test_upload_main_title_with_file_prefix(mock_site):
    files = {"f1": {"file_path": "/p1", "new_languages": 0}}

    res = upload_step(files, "File:Main.svg", site=mock_site)

    assert res["success"] is True


@patch("src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_unknown_error_status(mock_upload, mock_site):
    mock_upload.return_value = {"result": "SomethingWeird"}
    files = {"f1": {"file_path": "/p1", "file_name": "f1.svg", "new_languages": 1}}

    res = upload_step(files, "Main", site=mock_site)

    assert res["summary"]["failed"] == 1
    assert res["results"]["f1"]["result"] is False
