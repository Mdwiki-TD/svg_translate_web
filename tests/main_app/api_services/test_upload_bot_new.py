from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import mwclient.errors
import pytest
import requests

from src.main_app.api_services.upload_bot_new import UploadFile, _RETRY_DELAYS


# ══════════════════════════════════════════════════════════════════════════════
# fixtures & helpers
# ══════════════════════════════════════════════════════════════════════════════

def _err(message: str, error_details: str = "") -> dict[str, object]:
    return {"success": False, "error": message, "error_details": error_details}


@pytest.fixture
def site():
    return MagicMock()


@pytest.fixture
def tmp_file(tmp_path):
    """A real file on disk so Path.exists() returns True."""
    f = tmp_path / "test.jpg"
    f.write_bytes(b"fake image data")
    return f


@pytest.fixture
def uploader(site, tmp_file):
    return UploadFile(
        file_name="Test_file.jpg",
        file_path=tmp_file,
        site=site,
        summary="test summary",
        description="test description",
        new_file=False,
    )


def make_api_error(code: str, info: str = "") -> mwclient.errors.APIError:
    return mwclient.errors.APIError(code, info, {})


def make_upload_response(result: str = "Success") -> dict:
    return {"result": result, "filename": "Test_file.jpg"}


# ══════════════════════════════════════════════════════════════════════════════
# fix_file_name
# ══════════════════════════════════════════════════════════════════════════════

class TestFixFileName:
    def test_strips_file_prefix_lowercase(self, site, tmp_file):
        u = UploadFile("file:Test.jpg", tmp_file, site)
        assert u.file_name == "Test.jpg"

    def test_strips_file_prefix_uppercase(self, site, tmp_file):
        u = UploadFile("File:Test.jpg", tmp_file, site)
        assert u.file_name == "Test.jpg"

    def test_strips_file_prefix_mixed_case(self, site, tmp_file):
        u = UploadFile("FILE:Test.jpg", tmp_file, site)
        assert u.file_name == "Test.jpg"

    def test_strips_surrounding_whitespace(self, site, tmp_file):
        u = UploadFile("  Test.jpg  ", tmp_file, site)
        assert u.file_name == "Test.jpg"

    def test_no_prefix_unchanged(self, site, tmp_file):
        u = UploadFile("Test.jpg", tmp_file, site)
        assert u.file_name == "Test.jpg"

    def test_none_file_name_not_processed(self, site, tmp_file):
        u = UploadFile(None, tmp_file, site)
        assert u.file_name is None


# ══════════════════════════════════════════════════════════════════════════════
# _check_kwargs
# ══════════════════════════════════════════════════════════════════════════════

class TestCheckKwargs:
    def test_no_site(self, tmp_file):
        u = UploadFile("Test.jpg", tmp_file, site=None)
        assert u._check_kwargs() == _err("No site provided")

    def test_no_file_name(self, site, tmp_file):
        u = UploadFile(None, tmp_file, site)
        assert u._check_kwargs() == _err("File name is required")

    def test_no_file_path(self, site):
        u = UploadFile("Test.jpg", None, site)
        assert u._check_kwargs() == _err("File path is None")

    def test_existing_file_mode_file_not_on_commons(self, site, tmp_file):
        """new_file=False but page does not exist on Commons."""
        mock_page = MagicMock()
        mock_page.exists = False
        site.pages.__getitem__.return_value = mock_page
        u = UploadFile("Test.jpg", tmp_file, site, new_file=False)
        assert u._check_kwargs() == _err("File not found on Commons")

    def test_new_file_mode_file_already_on_commons(self, site, tmp_file):
        """new_file=True but page already exists on Commons."""
        mock_page = MagicMock()
        mock_page.exists = True
        site.pages.__getitem__.return_value = mock_page
        u = UploadFile("Test.jpg", tmp_file, site, new_file=True)
        assert u._check_kwargs() == _err("File already exists on Commons")

    def test_file_not_on_server(self, site):
        """Local file path does not exist."""
        mock_page = MagicMock()
        mock_page.exists = True
        site.pages.__getitem__.return_value = mock_page
        u = UploadFile("Test.jpg", Path("/nonexistent/path.jpg"), site, new_file=False)
        assert u._check_kwargs() == _err("File not found on server")

    def test_all_valid_existing_file(self, site, tmp_file):
        mock_page = MagicMock()
        mock_page.exists = True
        site.pages.__getitem__.return_value = mock_page
        u = UploadFile("Test.jpg", tmp_file, site, new_file=False)
        assert u._check_kwargs() == _err(None)

    def test_all_valid_new_file(self, site, tmp_file):
        mock_page = MagicMock()
        mock_page.exists = False
        site.pages.__getitem__.return_value = mock_page
        u = UploadFile("Test.jpg", tmp_file, site, new_file=True)
        assert u._check_kwargs() == _err(None)


# ══════════════════════════════════════════════════════════════════════════════
# _upload_file  (single attempt)
# ══════════════════════════════════════════════════════════════════════════════

class TestUploadFileInternal:
    def test_success(self, uploader):
        uploader._site_upload = MagicMock(return_value=make_upload_response())
        result = uploader._upload_file()
        assert result["result"] == "Success"
        assert "error" not in result

    def test_assert_user_failed(self, uploader):
        uploader._site_upload = MagicMock(side_effect=mwclient.errors.AssertUserFailedError())
        result = uploader._upload_file()
        assert result["error"] == "assertuserfailed"

    def test_user_blocked(self, uploader):
        uploader._site_upload = MagicMock(side_effect=mwclient.errors.UserBlocked(MagicMock()))
        result = uploader._upload_file()
        assert result["error"] == "userblocked"

    def test_insufficient_permission(self, uploader):
        uploader._site_upload = MagicMock(side_effect=mwclient.errors.InsufficientPermission(MagicMock()))
        result = uploader._upload_file()
        assert result["error"] == "insufficientpermission"

    def test_file_exists(self, uploader):
        uploader._site_upload = MagicMock(side_effect=mwclient.errors.FileExists("Test.jpg"))
        result = uploader._upload_file()
        assert result["error"] == "fileexists"

    def test_maximum_retries_exceeded(self, uploader):
        uploader._site_upload = MagicMock(side_effect=mwclient.errors.MaximumRetriesExceeded(MagicMock(), MagicMock()))
        result = uploader._upload_file()
        assert result["error"] == "maxretriesexceeded"

    def test_timeout(self, uploader):
        uploader._site_upload = MagicMock(side_effect=requests.exceptions.Timeout("timed out"))
        result = uploader._upload_file()
        assert result["error"] == "timeout"

    def test_connection_error(self, uploader):
        uploader._site_upload = MagicMock(side_effect=requests.exceptions.ConnectionError("refused"))
        result = uploader._upload_file()
        assert result["error"] == "connectionerror"

    def test_http_error(self, uploader):
        uploader._site_upload = MagicMock(side_effect=requests.exceptions.HTTPError("403"))
        result = uploader._upload_file()
        assert result["error"] == "httperror"

    def test_rate_limited(self, uploader):
        uploader._site_upload = MagicMock(side_effect=make_api_error("ratelimited"))
        result = uploader._upload_file()
        assert result["error"] == "ratelimited"

    def test_fileexists_no_change(self, uploader):
        uploader._site_upload = MagicMock(side_effect=make_api_error("fileexists-no-change"))
        result = uploader._upload_file()
        assert result["error"] == "fileexists-no-change"

    def test_other_api_error(self, uploader):
        uploader._site_upload = MagicMock(side_effect=make_api_error("badtoken", "Invalid token"))
        result = uploader._upload_file()
        assert result["error"] == "badtoken"
        assert "error_details" in result

    def test_unexpected_exception(self, uploader):
        uploader._site_upload = MagicMock(side_effect=Exception("something broke"))
        result = uploader._upload_file()
        assert result["error"] == "unexpected"
        assert "something broke" in result["error_details"]


# ══════════════════════════════════════════════════════════════════════════════
# _upload_with_retry
# ══════════════════════════════════════════════════════════════════════════════

class TestUploadWithRetry:
    def test_succeeds_on_first_retry(self, uploader):
        uploader._upload_file = MagicMock(return_value=make_upload_response())
        with patch("src.main_app.api_services.upload_bot_new.time.sleep"):
            result = uploader._upload_with_retry()
        assert result["result"] == "Success"

    def test_exhausts_all_retries(self, uploader):
        uploader._upload_file = MagicMock(return_value=_err("ratelimited", ""))
        with patch("src.main_app.api_services.upload_bot_new.time.sleep"):
            result = uploader._upload_with_retry()
        assert result["error"] == "ratelimited"
        assert uploader._upload_file.call_count == len(_RETRY_DELAYS)

    def test_sleeps_correct_delays(self, uploader):
        uploader._upload_file = MagicMock(return_value=_err("ratelimited", ""))
        with patch("src.main_app.api_services.upload_bot_new.time.sleep") as mock_sleep:
            uploader._upload_with_retry()
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == list(_RETRY_DELAYS)

    def test_stops_early_on_non_ratelimited_error(self, uploader):
        """If a non-ratelimited error occurs during retry, return it immediately."""
        uploader._upload_file = MagicMock(side_effect=[
            _err("ratelimited", ""),
            _err("userblocked", "User is blocked"),
        ])
        with patch("src.main_app.api_services.upload_bot_new.time.sleep"):
            result = uploader._upload_with_retry()
        assert result["error"] == "userblocked"
        assert uploader._upload_file.call_count == 2

    def test_succeeds_on_second_retry(self, uploader):
        uploader._upload_file = MagicMock(side_effect=[
            _err("ratelimited", ""),
            _err("ratelimited", ""),
            make_upload_response(),
        ])
        with patch("src.main_app.api_services.upload_bot_new.time.sleep"):
            result = uploader._upload_with_retry()
        assert result["result"] == "Success"
        assert uploader._upload_file.call_count == 3


# ══════════════════════════════════════════════════════════════════════════════
# upload  (full flow)
# ══════════════════════════════════════════════════════════════════════════════

class TestUpload:
    def _make_uploader(self, site, tmp_file, new_file=False):
        mock_page = MagicMock()
        mock_page.exists = not new_file  # exists=True for update, False for new
        site.pages.__getitem__.return_value = mock_page
        return UploadFile("Test.jpg", tmp_file, site, new_file=new_file)

    def test_success(self, site, tmp_file):
        u = self._make_uploader(site, tmp_file)
        u._site_upload = MagicMock(return_value=make_upload_response())
        with patch("builtins.open", mock_open(read_data=b"data")):
            result = u.upload()
        assert result["result"] == "Success"

    def test_check_kwargs_fails_early(self, site, tmp_file):
        """upload() returns error immediately if _check_kwargs fails."""
        u = UploadFile("Test.jpg", tmp_file, site=None)
        result = u.upload()
        assert result == _err("No site provided")

    def test_rate_limited_then_success(self, site, tmp_file):
        u = self._make_uploader(site, tmp_file)
        u._upload_file = MagicMock(side_effect=[
            _err("ratelimited", ""),
            make_upload_response(),
        ])
        with patch("src.main_app.api_services.upload_bot_new.time.sleep"):
            result = u.upload()
        assert result["result"] == "Success"

    def test_rate_limited_exhausts_all_retries(self, site, tmp_file):
        u = self._make_uploader(site, tmp_file)
        u._upload_file = MagicMock(return_value=_err("ratelimited", ""))
        with patch("src.main_app.api_services.upload_bot_new.time.sleep"):
            result = u.upload()
        assert result["error"] == "ratelimited"
        # 1 initial attempt + len(_RETRY_DELAYS) retries
        assert u._upload_file.call_count == 1 + len(_RETRY_DELAYS)

    def test_rate_limited_sleeps_correct_delays(self, site, tmp_file):
        u = self._make_uploader(site, tmp_file)
        u._upload_file = MagicMock(return_value=_err("ratelimited", ""))
        with patch("src.main_app.api_services.upload_bot_new.time.sleep") as mock_sleep:
            u.upload()
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == list(_RETRY_DELAYS)

    def test_non_ratelimited_error_no_retry(self, site, tmp_file):
        """Errors other than ratelimited should not trigger retry."""
        u = self._make_uploader(site, tmp_file)
        u._upload_file = MagicMock(return_value=_err("userblocked", ""))
        with patch("src.main_app.api_services.upload_bot_new.time.sleep") as mock_sleep:
            result = u.upload()
        assert result["error"] == "userblocked"
        mock_sleep.assert_not_called()
        assert u._upload_file.call_count == 1

    def test_new_file_upload_success(self, site, tmp_file):
        u = self._make_uploader(site, tmp_file, new_file=True)
        u._site_upload = MagicMock(return_value=make_upload_response())
        with patch("builtins.open", mock_open(read_data=b"data")):
            result = u.upload()
        assert result["result"] == "Success"
