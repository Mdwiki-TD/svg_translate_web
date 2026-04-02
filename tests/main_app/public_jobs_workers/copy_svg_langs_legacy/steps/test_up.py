from unittest.mock import MagicMock, patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.steps.upload import upload_step


@pytest.fixture
def mock_site():
    return MagicMock()


@pytest.fixture
def mock_store():
    return MagicMock()


def test_upload_task_disabled(mock_site):
    stages = {}
    res = upload_step({}, "Main", site=mock_site)
    assert res["success"] is True
    assert res["summary"]["total"] == 0


def test_upload_task_no_files(mock_site):
    stages = {}
    res = upload_step({}, "Main", site=mock_site)
    assert res["success"] is True
    assert res["summary"]["total"] == 0


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.upload.upload_file")
def test_upload_task_success(mock_upload, mock_site):
    mock_upload.return_value = {"result": "Success"}

    stages = {}
    files = {"f1": {"file_path": "/path/to/f1.svg", "new_languages": 1}}

    res = upload_step(files, "Main", site=mock_site)

    assert res["summary"]["uploaded"] == 1
    mock_upload.assert_called_once()
