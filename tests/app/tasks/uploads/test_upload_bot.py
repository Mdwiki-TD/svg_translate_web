import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.main_app.tasks.uploads.upload_bot import upload_file

@pytest.fixture
def mock_site():
    site = MagicMock()
    return site

def test_upload_file_no_site():
    res = upload_file("file.svg", "/path/to/file", site=None)
    assert res == {"error": "No site provided"}

@patch("src.app.tasks.uploads.upload_bot.Path")
def test_upload_file_not_found_on_commons(mock_path_cls, mock_site):
    mock_site.Pages.__getitem__.return_value.exists = False

    res = upload_file("file.svg", "/path/to/file", site=mock_site)
    assert res == {"error": "File not found on Commons"}

@patch("src.app.tasks.uploads.upload_bot.Path")
def test_upload_file_not_found_on_server(mock_path_cls, mock_site):
    mock_site.Pages.__getitem__.return_value.exists = True
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = False
    mock_path_cls.return_value = mock_path_instance

    res = upload_file("file.svg", "/path/to/file", site=mock_site)
    assert res == {"error": "File not found on server"}

@patch("src.app.tasks.uploads.upload_bot.open", create=True)
@patch("src.app.tasks.uploads.upload_bot.Path")
def test_upload_file_success(mock_path_cls, mock_open, mock_site):
    mock_site.Pages.__getitem__.return_value.exists = True
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_cls.return_value = mock_path_instance

    mock_site.upload.return_value = {"result": "Success"}

    res = upload_file("file.svg", "/path/to/file", site=mock_site)
    assert res["result"] == "Success"
    mock_site.upload.assert_called_once()

@patch("src.app.tasks.uploads.upload_bot.open", create=True)
@patch("src.app.tasks.uploads.upload_bot.Path")
def test_upload_file_fileexists_no_change(mock_path_cls, mock_open, mock_site):
    mock_site.Pages.__getitem__.return_value.exists = True
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_cls.return_value = mock_path_instance

    mock_site.upload.side_effect = Exception("fileexists-no-change")

    res = upload_file("file.svg", "/path/to/file", site=mock_site)
    assert res == {"error": "fileexists-no-change"}
