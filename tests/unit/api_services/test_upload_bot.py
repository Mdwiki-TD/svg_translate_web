from __future__ import annotations

from unittest.mock import MagicMock, patch

import mwclient.errors
import pytest

from src.main_app.api_services.upload_bot import upload_file

# ══════════════════════════════════════════════════════════════════════════════
# fixtures & helpers
# ══════════════════════════════════════════════════════════════════════════════


def _err(message: str, error_details: str = "") -> dict[str, object]:
    return {"success": False, "error": message, "error_details": error_details}


@pytest.fixture
def mock_site():
    return MagicMock()


@pytest.fixture
def tmp_file(tmp_path):
    """A real file on disk so Path.exists() returns True."""
    f = tmp_path / "test.jpg"
    f.write_bytes(b"fake image data")
    return f


def test_upload_file_no_site():
    res = upload_file("file.svg", "/path/to/file", site=None)
    assert res == _err("No site provided")


@patch("src.main_app.api_services.upload_bot.Path")
def test_upload_file_not_found_on_commons(mock_path_cls, mock_site):
    mock_site.pages.__getitem__.return_value.exists = False

    res = upload_file("file.svg", "/path/to/file", site=mock_site)
    assert res == _err("File not found on Commons")


# @patch("src.main_app.api_services.upload_bot.Path")
def test_upload_file_not_found_on_server(mock_site):
    """Local file path does not exist."""
    mock_page = MagicMock()
    mock_page.exists = True
    mock_site.pages.__getitem__.return_value = mock_page

    res = upload_file("file.svg", "/nonexistent/path.jpg", site=mock_site, new_file=False)
    assert res == _err("File not found")


@patch("src.main_app.api_services.upload_bot.open", create=True)
@patch("src.main_app.api_services.upload_bot.Path")
def test_upload_file_success(mock_path_cls, mock_open, mock_site):
    mock_site.pages.__getitem__.return_value.exists = True
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_cls.return_value = mock_path_instance

    mock_site.upload.return_value = {"result": "Success"}

    res = upload_file("file.svg", "/path/to/file", site=mock_site)
    assert res["result"] == "Success"
    mock_site.upload.assert_called_once()


@patch("src.main_app.api_services.upload_bot.open", create=True)
@patch("src.main_app.api_services.upload_bot.Path")
def test_upload_file_fileexists_no_change(mock_path_cls, mock_open, mock_site):
    mock_site.pages.__getitem__.return_value.exists = True
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_cls.return_value = mock_path_instance

    mock_site.upload.side_effect = mwclient.errors.APIError(
        "fileexists-no-change", "The upload is an exact duplicate of the current version of [[:File:svg.png]].", {}
    )

    res = upload_file("File.svg", "/path/to/file", site=mock_site)
    assert res == _err("fileexists-no-change")
