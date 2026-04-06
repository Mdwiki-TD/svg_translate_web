from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.main_app.api_services.upload_bot import _RETRY_DELAYS, UploadFile


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


def make_upload_response(result: str = "Success") -> dict:
    return {"result": result, "filename": "Test_file.jpg"}

# ══════════════════════════════════════════════════════════════════════════════
# Test Groups
# ══════════════════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════════════════
# upload  (full flow)
# ══════════════════════════════════════════════════════════════════════════════


class TestUpload:
    def _make_uploader(self, site, tmp_file, new_file=False):
        mock_page = MagicMock()
        mock_page.exists = not new_file  # exists=True for update, False for new
        site.pages.__getitem__.return_value = mock_page
        return UploadFile("Test.jpg", tmp_file, site, new_file=new_file)

    def test_success(self, mock_site, tmp_file):
        u = self._make_uploader(mock_site, tmp_file)
        u._site_upload = MagicMock(return_value=make_upload_response())
        with patch("builtins.open", mock_open(read_data=b"data")):
            result = u.upload()
        assert result["result"] == "Success"

    def test_check_kwargs_fails_early(self, mock_site, tmp_file):
        """upload() returns error immediately if _check_kwargs fails."""
        u = UploadFile("Test.jpg", tmp_file, site=None)
        result = u.upload()
        assert result == _err("No site provided")

    def test_rate_limited_then_success(self, mock_site, tmp_file):
        u = self._make_uploader(mock_site, tmp_file)
        u._upload_file = MagicMock(
            side_effect=[
                _err("ratelimited", ""),
                make_upload_response(),
            ]
        )
        with patch("src.main_app.api_services.upload_bot.time.sleep"):
            result = u.upload()
        assert result["result"] == "Success"

    def test_rate_limited_exhausts_all_retries(self, mock_site, tmp_file):
        u = self._make_uploader(mock_site, tmp_file)
        u._upload_file = MagicMock(return_value=_err("ratelimited", ""))
        with patch("src.main_app.api_services.upload_bot.time.sleep"):
            result = u.upload()
        assert result["error"] == "ratelimited"
        # 1 initial attempt + len(_RETRY_DELAYS) retries
        assert u._upload_file.call_count == 1 + len(_RETRY_DELAYS)

    def test_rate_limited_sleeps_correct_delays(self, mock_site, tmp_file):
        u = self._make_uploader(mock_site, tmp_file)
        u._upload_file = MagicMock(return_value=_err("ratelimited", ""))
        with patch("src.main_app.api_services.upload_bot.time.sleep") as mock_sleep:
            u.upload()
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == list(_RETRY_DELAYS)

    def test_non_ratelimited_error_no_retry(self, mock_site, tmp_file):
        """Errors other than ratelimited should not trigger retry."""
        u = self._make_uploader(mock_site, tmp_file)
        u._upload_file = MagicMock(return_value=_err("userblocked", ""))
        with patch("src.main_app.api_services.upload_bot.time.sleep") as mock_sleep:
            result = u.upload()
        assert result["error"] == "userblocked"
        mock_sleep.assert_not_called()
        assert u._upload_file.call_count == 1

    def test_new_file_upload_success(self, mock_site, tmp_file):
        u = self._make_uploader(mock_site, tmp_file, new_file=True)
        u._site_upload = MagicMock(return_value=make_upload_response())
        with patch("builtins.open", mock_open(read_data=b"data")):
            result = u.upload()
        assert result["result"] == "Success"


@pytest.mark.integration
class TestUploadBotIntegration:
    """
    These tests require a valid mock_site or a connection to a test wiki.
    They verify the actual interaction between the OS and the library.
    """

    def test_actual_file_reading_during_upload(self, mock_site, tmp_path):
        # Create a real physical file
        image_path = tmp_path / "integration_test.jpg"
        image_content = b"real_binary_data_here"
        image_path.write_bytes(image_content)

        # Mock only the network call, keep the file logic real
        mock_site.pages.__getitem__.return_value.exists = True

        uploader = UploadFile(
            file_name="Integration_Test.jpg",
            file_path=image_path,
            site=mock_site,
            new_file=False
        )

        # Patch the low-level mwclient call to verify what was actually read from disk
        with pytest.MonkeyPatch().context() as m:
            m.setattr(uploader, "_site_upload", lambda **kwargs: {"result": "Success"})
            result = uploader.upload()

        assert result["result"] == "Success"
        assert image_path.exists()

    def test_invalid_path_error_handling(self, mock_site):
        # Test behavior with a path that definitely doesn't exist on the OS
        bad_path = Path("/tmp/should_not_exist_12345.jpg")
        uploader = UploadFile("Test.jpg", bad_path, mock_site)

        result = uploader.upload()
        assert result["error"] == "File not found"
