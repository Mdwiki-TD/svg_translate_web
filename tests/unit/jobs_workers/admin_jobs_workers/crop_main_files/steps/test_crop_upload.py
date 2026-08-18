"""Unit tests for crop_main_files.steps.upload module."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest

from src.main_app.api_services.files_service.objects import UploadResult
from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.steps import upload


@pytest.fixture
def mock_upload_class(monkeypatch):
    """Mock the UploadFileNew class so constructor args are captured."""
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.api_services.files_service.uploader.UploadFileNew",
        _mock,
    )
    return _mock


class TestUploadCroppedFile:
    """Unit tests for upload_cropped_file function."""

    def test_upload_cropped_file_success(self, mock_upload_class, tmp_path):
        """Test successful upload of a cropped file."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is True
        assert result["cropped_filename"] == cropped_filename
        assert result["error"] is None

        # Verify UploadFileNew was constructed with correct parameters
        mock_upload_class.return_value.upload_obj.assert_called_once_with(
            file_name="test (cropped).svg",
            file_path=cropped_path,
            summary="[[:File:test.svg]] cropped to remove the footer.",
            new_file=True,
            description=None,
        )

    def test_upload_cropped_file_no_site(self, mock_upload_class, tmp_path):
        """Test upload fails when no site is provided."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        site = None

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is False
        assert result["error"] == "Failed to authenticate with Commons"
        assert result["cropped_filename"] == cropped_filename

    def test_upload_cropped_file_exception_during_upload(self, mock_upload_class, tmp_path):
        """Test handling of exceptions during upload."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.side_effect = RuntimeError("Network timeout")

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is False
        assert "Exception during upload" in result["error"]
        assert "Network timeout" in result["error"]
        assert result["cropped_filename"] == cropped_filename

    def test_upload_cropped_file_strips_file_prefix(self, mock_upload_class, tmp_path):
        """Test that 'File:' prefix is stripped from filename during upload."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        upload.upload_cropped_file(cropped_filename, cropped_path, site)

        # Verify the File: prefix was stripped
        call_args = mock_upload_class.return_value.upload_obj.call_args[1]
        assert call_args["file_name"] == "test (cropped).svg"
        assert not call_args["file_name"].startswith("File:")

    def test_upload_cropped_file_without_file_prefix(self, mock_upload_class, tmp_path):
        """Test upload with filename that doesn't have 'File:' prefix."""
        cropped_filename = "test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is True
        # Should use the filename as-is
        call_args = mock_upload_class.return_value.upload_obj.call_args[1]
        assert call_args["file_name"] == "test (cropped).svg"

    def test_upload_cropped_file_with_special_characters(self, mock_upload_class, tmp_path):
        """Test upload with filename containing special characters."""
        cropped_filename = "File:test & image (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is True
        call_args = mock_upload_class.return_value.upload_obj.call_args[1]
        assert call_args["file_name"] == "test & image (cropped).svg"

    def test_upload_cropped_file_uses_new_file_flag(self, mock_upload_class, tmp_path):
        """Test that upload is called with new_file=True."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        upload.upload_cropped_file(cropped_filename, cropped_path, site)

        # Verify new_file=True is set
        call_args = mock_upload_class.return_value.upload_obj.call_args[1]
        assert call_args["new_file"] is True

    def test_upload_cropped_file_uses_correct_summary(self, mock_upload_class, tmp_path):
        """Test that upload uses correct summary text."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        upload.upload_cropped_file(cropped_filename, cropped_path, site)

        # Verify summary is correct
        call_args = mock_upload_class.return_value.upload_obj.call_args[1]
        assert call_args["summary"] == "[[:File:test.svg]] cropped to remove the footer."

    def test_upload_cropped_file_returns_filename_in_result(self, mock_upload_class, tmp_path):
        """Test that result always includes the cropped filename."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        site = None

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        # Even on failure, filename should be in result
        assert result["cropped_filename"] == cropped_filename

    def test_upload_cropped_file_with_very_long_filename(self, mock_upload_class, tmp_path):
        """Test upload with a very long filename."""
        long_name = "a" * 200
        cropped_filename = f"File:{long_name} (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is True

    def test_upload_cropped_file_upload_result_missing_keys(self, mock_upload_class, tmp_path):
        """Test handling when upload_file returns result without expected keys."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        # Return a result without 'error' key
        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=False)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is False
        # Should handle missing 'error' key gracefully
        assert "Unknown upload error" in result["error"]

    def test_upload_cropped_file_with_unicode_filename(self, mock_upload_class, tmp_path):
        """Test upload with filename containing unicode characters."""
        cropped_filename = "File:测试图片 (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is True
        call_args = mock_upload_class.return_value.upload_obj.call_args[1]
        assert "测试图片" in call_args["file_name"]

    def test_upload_cropped_file_with_path_object(self, mock_upload_class, tmp_path):
        """Test upload works with Path object for cropped_path."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is True
        # Verify Path object was passed correctly
        call_args = mock_upload_class.return_value.upload_obj.call_args[1]
        assert call_args["file_path"] == cropped_path

    def test_upload_cropped_file_empty_filename(self, mock_upload_class, tmp_path):
        """Test upload with empty filename."""
        cropped_filename = ""
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        # Should still attempt upload, but with empty filename
        assert result["success"] is True

    def test_upload_cropped_file_with_wikitext(self, mock_upload_class, tmp_path):
        """Test upload with wikitext parameter."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()
        wikitext = "==Summary==\nTest description"

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=True)

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site, wikitext)

        assert result["success"] is True
        call_args = mock_upload_class.return_value.upload_obj.call_args[1]
        assert call_args["description"] == wikitext

    def test_upload_cropped_file_upload_fails(self, mock_upload_class, tmp_path):
        """Test handling of upload failure."""
        cropped_filename = "File:test (cropped).svg"
        cropped_path = tmp_path / "test_cropped.svg"
        cropped_path.write_text("<svg></svg>")
        site = Mock()

        mock_upload_class.return_value.upload_obj.return_value = UploadResult(ok=False, error="File already exists")

        result = upload.upload_cropped_file(cropped_filename, cropped_path, site)

        assert result["success"] is False
        assert "Upload failed" in result["error"]
        assert "File already exists" in result["error"]
        assert result["cropped_filename"] == cropped_filename
