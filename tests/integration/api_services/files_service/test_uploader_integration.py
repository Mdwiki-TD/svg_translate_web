from __future__ import annotations

from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.main_app.api_services.files_service.objects import FileData
from src.main_app.api_services.files_service.uploader import _RETRY_DELAYS, FileUploader


@pytest.fixture(autouse=True)
def mock_sleep(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.api_services.files_service.uploader.time.sleep",
        _mock,
    )
    return _mock


def _err(message: str | None, error_details: str = "") -> dict[str, object]:
    """Helper to match the expected return structure of FileUploader."""
    return {"success": False, "error": message, "error_details": error_details}


@pytest.fixture
def tmp_file(tmp_path):
    """A real file on disk so Path.exists() returns True for unit logic."""
    f = tmp_path / "test.jpg"
    f.write_bytes(b"fake image data")
    return f


def make_upload_response(result: str = "success") -> dict[str, Any]:
    return {"result": result, "filename": "Test_file.jpg"}


# ══════════════════════════════════════════════════════════════════════════════
# upload  (full flow)
# ══════════════════════════════════════════════════════════════════════════════


class TestUpload:
    def _make_uploader(self, site, new_file=False):
        mock_p = MagicMock()
        mock_p.exists = not new_file  # exists=True for update, False for new
        site.pages.__getitem__.return_value = mock_p
        return FileUploader(site=site)
        # return FileUploader("Test.jpg", tmp_file, site, new_file=new_file)

    def test_check_kwargs_fails_early(self, mock_site, tmp_file):
        """upload() returns error immediately if _check_kwargs fails."""
        u = FileUploader(None)

        data = FileData.from_dict(file_name="Test.jpg", file_path=tmp_file)
        result = u.upload(data)
        assert result == _err("No site provided")

    def test_rate_limited_then_success(self, mock_site, tmp_file):
        u = self._make_uploader(mock_site)
        u._upload_file = MagicMock(
            side_effect=[
                _err("ratelimited", ""),
                make_upload_response(),
            ]
        )

        data = FileData.from_dict(file_name="Test.jpg", file_path=tmp_file)
        result = u.upload(data)
        assert result["result"] == "success"

    def test_rate_limited_exhausts_all_retries(self, mock_site, tmp_file):
        u = self._make_uploader(mock_site)
        u._upload_file = MagicMock(return_value=_err("ratelimited", ""))

        data = FileData.from_dict(file_name="Test.jpg", file_path=tmp_file)
        result = u.upload(data)
        assert result["error"] == "ratelimited"
        # 1 initial attempt + len(_RETRY_DELAYS) retries
        assert u._upload_file.call_count == 1 + len(_RETRY_DELAYS)

    def test_rate_limited_sleeps_correct_delays(self, mock_site, tmp_file, mock_sleep):
        u = self._make_uploader(mock_site)
        u._upload_file = MagicMock(return_value=_err("ratelimited", ""))

        data = FileData.from_dict(file_name="Test.jpg", file_path=tmp_file)
        u.upload(data)
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert sleep_calls == list(_RETRY_DELAYS)

    def test_non_ratelimited_error_no_retry(self, mock_site, tmp_file, mock_sleep):
        """Errors other than ratelimited should not trigger retry."""
        u = self._make_uploader(mock_site)
        u._upload_file = MagicMock(return_value=_err("userblocked", ""))

        data = FileData.from_dict(file_name="Test.jpg", file_path=tmp_file)
        result = u.upload(data)
        assert result["error"] == "userblocked"
        mock_sleep.assert_not_called()
        assert u._upload_file.call_count == 1

    def test_new_file_upload_success(self, mock_site, tmp_file):
        u = self._make_uploader(mock_site, new_file=True)
        u._site_upload = MagicMock(return_value=make_upload_response())

        data = FileData.from_dict(file_name="Test.jpg", file_path=tmp_file, new_file=True)

        with patch("builtins.open", mock_open(read_data=b"data")):
            result = u.upload(data)

        assert result["result"] == "success"


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

        def fake_upload(*, file, **kwargs):
            assert file.read() == image_content
            return {"result": "success"}

        mock_site.upload.side_effect = fake_upload

        uploader = FileUploader(mock_site)

        data = FileData.from_dict(file_name="Integration_Test.jpg", file_path=image_path, new_file=False)

        result = uploader.upload(data)

        assert result["result"] == "success"
        assert image_path.exists()

    def test_invalid_path_error_handling(self, mock_site, tmp_path):
        # Test behavior with a path that definitely doesn't exist on the OS
        bad_path = tmp_path / "should_not_exist_12345.jpg"
        uploader = FileUploader(mock_site)

        data = FileData.from_dict(file_name="Test.jpg", file_path=bad_path)

        result = uploader.upload(data)
        assert result["error"] == "File not found"
