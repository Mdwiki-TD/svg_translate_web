from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import mwclient.errors
import pytest
import requests

from src.main_app.api_services.upload_bot import _RETRY_DELAYS, UploadFile

# ══════════════════════════════════════════════════════════════════════════════
# Fixtures & Helpers
# ══════════════════════════════════════════════════════════════════════════════


def _err(message: str | None, error_details: str = "") -> dict[str, object]:
    """Helper to match the expected return structure of UploadFile."""
    return {"success": False, "error": message, "error_details": error_details}


@pytest.fixture
def mock_site():
    return MagicMock()


@pytest.fixture
def tmp_file(tmp_path):
    """A real file on disk so Path.exists() returns True for unit logic."""
    f = tmp_path / "test.jpg"
    f.write_bytes(b"fake image data")
    return f


@pytest.fixture
def uploader(mock_site, tmp_file):
    """Standard uploader instance with mocks."""
    return UploadFile(
        file_name="Test_file.jpg",
        file_path=tmp_file,
        site=mock_site,
        summary="test summary",
        description="test description",
        new_file=False,
    )


def make_api_error(code: str, info: str = "") -> mwclient.errors.APIError:
    return mwclient.errors.APIError(code, info, {})


def make_upload_response(result: str = "Success") -> dict:
    return {"result": result, "filename": "Test_file.jpg"}

# ══════════════════════════════════════════════════════════════════════════════
# Test Groups
# ══════════════════════════════════════════════════════════════════════════════


class TestFixFileName:
    @pytest.mark.parametrize("input_name, expected", [
        ("file:Test.jpg", "Test.jpg"),
        ("File:Test.jpg", "Test.jpg"),
        ("FILE:Test.jpg", "Test.jpg"),
        ("  Test.jpg  ", "Test.jpg"),
        ("Test.jpg", "Test.jpg"),
    ])
    def test_filename_cleaning(self, input_name, expected, mock_site, tmp_file):
        u = UploadFile(input_name, tmp_file, mock_site)
        assert u.file_name == expected

    def test_none_file_name_not_processed(self, mock_site, tmp_file):
        u = UploadFile(None, tmp_file, mock_site)
        assert u.file_name is None


# ══════════════════════════════════════════════════════════════════════════════
# _check_kwargs
# ══════════════════════════════════════════════════════════════════════════════


class TestCheckKwargs:
    def test_no_site(self, tmp_file):
        u = UploadFile("Test.jpg", tmp_file, site=None)
        assert u._check_kwargs() == _err("No site provided")

    def test_no_file_name(self, mock_site, tmp_file):
        u = UploadFile(None, tmp_file, mock_site)
        assert u._check_kwargs() == _err("File name is required")

    def test_no_file_path(self, mock_site):
        u = UploadFile("Test.jpg", None, mock_site)
        assert u._check_kwargs() == _err("File path is None")

    def test_existing_file_mode_not_on_commons(self, mock_site, tmp_file):
        mock_site.pages.__getitem__.return_value.exists = False
        u = UploadFile("Test.jpg", tmp_file, mock_site, new_file=False)
        assert u._check_kwargs() == _err("File not found on Commons")

    def test_new_file_mode_already_on_commons(self, mock_site, tmp_file):
        mock_site.pages.__getitem__.return_value.exists = True
        u = UploadFile("Test.jpg", tmp_file, mock_site, new_file=True)
        assert u._check_kwargs() == _err("File already exists on Commons")

    def test_file_not_on_local_filesystem(self, mock_site):
        mock_site.pages.__getitem__.return_value.exists = True
        u = UploadFile("Test.jpg", Path("/nonexistent/path.jpg"), mock_site, new_file=False)
        assert u._check_kwargs() == _err("File not found")

    def test_all_valid_existing_file(self, mock_site, tmp_file):
        mock_page = MagicMock()
        mock_page.exists = True
        mock_site.pages.__getitem__.return_value = mock_page
        u = UploadFile("Test.jpg", tmp_file, mock_site, new_file=False)
        assert u._check_kwargs() == _err(None)

    def test_all_valid_new_file(self, mock_site, tmp_file):
        mock_page = MagicMock()
        mock_page.exists = False
        mock_site.pages.__getitem__.return_value = mock_page
        u = UploadFile("Test.jpg", tmp_file, mock_site, new_file=True)
        assert u._check_kwargs() == _err(None)


# ══════════════════════════════════════════════════════════════════════════════
# _upload_file  (single attempt)
# ══════════════════════════════════════════════════════════════════════════════


class TestUploadFileInternal:
    """Tests the error handling mapping in _upload_file."""

    def test_success(self, uploader):
        uploader._site_upload = MagicMock(return_value=make_upload_response())
        result = uploader._upload_file()
        assert result["result"] == "Success"
        assert "error" not in result

    @pytest.mark.parametrize("exception, expected_code", [
        (mwclient.errors.AssertUserFailedError(), "assertuserfailed"),
        (mwclient.errors.UserBlocked(MagicMock()), "userblocked"),
        (mwclient.errors.InsufficientPermission(MagicMock()), "insufficientpermission"),
        (mwclient.errors.FileExists("Test.jpg"), "fileexists"),
        (mwclient.errors.MaximumRetriesExceeded(MagicMock(), MagicMock()), "maxretriesexceeded"),
        (requests.exceptions.Timeout("timed out"), "timeout"),
        (requests.exceptions.ConnectionError("refused"), "connectionerror"),
        (requests.exceptions.HTTPError("403"), "httperror"),
        (make_api_error("ratelimited"), "ratelimited"),
        (make_api_error("fileexists-no-change"), "fileexists-no-change"),
    ])
    def test_exception_mapping(self, uploader, exception, expected_code):
        uploader._site_upload = MagicMock(side_effect=exception)
        result = uploader._upload_file()
        assert result["error"] == expected_code

    def test_other_api_error(self, uploader):
        uploader._site_upload = MagicMock(side_effect=make_api_error("badtoken", "Invalid token"))
        result = uploader._upload_file()
        assert result["error"] == "badtoken"
        assert "error_details" in result

    def test_unexpected_exception(self, uploader):
        uploader._site_upload = MagicMock(side_effect=RuntimeError("boom"))
        result = uploader._upload_file()
        assert result["error"] == "unexpected"
        assert "boom" in str(result["error_details"])


# ══════════════════════════════════════════════════════════════════════════════
# _upload_with_retry
# ══════════════════════════════════════════════════════════════════════════════


class TestUploadWithRetry:
    def test_succeeds_on_first_retry(self, uploader):
        uploader._upload_file = MagicMock(return_value=make_upload_response())
        with patch("src.main_app.api_services.upload_bot.time.sleep"):
            result = uploader._upload_with_retry()
        assert result["result"] == "Success"

    def test_exhausts_all_retries(self, uploader):
        uploader._upload_file = MagicMock(return_value=_err("ratelimited", ""))
        with patch("src.main_app.api_services.upload_bot.time.sleep"):
            result = uploader._upload_with_retry()
        assert result["error"] == "ratelimited"
        assert uploader._upload_file.call_count == len(_RETRY_DELAYS)

    def test_sleeps_correct_delays(self, uploader):
        uploader._upload_file = MagicMock(return_value=_err("ratelimited", ""))
        with patch("src.main_app.api_services.upload_bot.time.sleep") as mock_sleep:
            uploader._upload_with_retry()
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == list(_RETRY_DELAYS)

    def test_stops_early_on_non_ratelimited_error(self, uploader):
        """If a non-ratelimited error occurs during retry, return it immediately."""
        uploader._upload_file = MagicMock(
            side_effect=[
                _err("ratelimited", ""),
                _err("userblocked", "User is blocked"),
            ]
        )
        with patch("src.main_app.api_services.upload_bot.time.sleep"):
            result = uploader._upload_with_retry()
        assert result["error"] == "userblocked"
        assert uploader._upload_file.call_count == 2

    def test_succeeds_on_second_retry(self, uploader):
        uploader._upload_file = MagicMock(
            side_effect=[
                _err("ratelimited", ""),
                _err("ratelimited", ""),
                make_upload_response(),
            ]
        )
        with patch("src.main_app.api_services.upload_bot.time.sleep"):
            result = uploader._upload_with_retry()
        assert result["result"] == "Success"
        assert uploader._upload_file.call_count == 3
