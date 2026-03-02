"""
Comprehensive unit tests for download_task module.
Tests cover download functionality, and error handling.
"""

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.api_services.download_file_utils import download_commons_svgs


@pytest.fixture
def mock_requests_session():
    """Create a mock requests session."""
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.content = b"<svg>test</svg>"
    session.get.return_value = response
    return session


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


class TestDownloadCommonsSvgs:
    """Test download_commons_svgs function."""

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_single_file(self, mock_download_core, temp_output_dir):
        """Test downloading a single SVG file."""
        mock_download_core.return_value = b"<svg>content</svg>"

        titles = ["Example.svg"]
        result = download_commons_svgs(titles, temp_output_dir)

        assert len(result) == 1
        assert (temp_output_dir / "Example.svg").exists()

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_multiple_files(self, mock_download_core, temp_output_dir):
        """Test downloading multiple SVG files."""
        mock_download_core.return_value = b"<svg>content</svg>"

        titles = ["File1.svg", "File2.svg", "File3.svg"]
        result = download_commons_svgs(titles, temp_output_dir)

        assert len(result) == 3
        for title in titles:
            assert (temp_output_dir / title).exists()

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_skips_existing_files(self, mock_download_core, temp_output_dir):
        """Test that existing files are skipped."""
        # Create existing file
        existing_file = temp_output_dir / "Existing.svg"
        existing_file.write_bytes(b"<svg>old content</svg>")

        titles = ["Existing.svg"]
        result = download_commons_svgs(titles, temp_output_dir)

        # Should not download, file already exists
        mock_download_core.assert_not_called()
        assert len(result) == 1
        # Content should remain unchanged
        assert existing_file.read_bytes() == b"<svg>old content</svg>"

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_handles_network_error(self, mock_download_core, temp_output_dir):
        """Test handling of network errors."""
        import requests

        mock_download_core.side_effect = requests.exceptions.RequestException("Network error")

        titles = ["NetworkError.svg"]
        result = download_commons_svgs(titles, temp_output_dir)

        # Should return empty list for failed downloads
        assert len(result) == 0

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_handles_404_error(self, mock_download_core, temp_output_dir):
        """Test handling of 404 not found errors."""
        import requests

        mock_download_core.side_effect = requests.exceptions.HTTPError("404 Not Found")

        titles = ["NotFound.svg"]
        result = download_commons_svgs(titles, temp_output_dir)

        # File should not be in result
        assert len(result) == 0

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_empty_list(self, mock_download_core, temp_output_dir):
        """Test downloading with empty titles list."""
        result = download_commons_svgs([], temp_output_dir)

        assert len(result) == 0
        mock_download_core.assert_not_called()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_with_special_characters_in_filename(self, mock_download_core, temp_output_dir):
        """Test downloading files with special characters in names."""
        mock_download_core.return_value = b"<svg>content</svg>"

        titles = ["File with spaces.svg", "File-with-dashes.svg"]
        result = download_commons_svgs(titles, temp_output_dir)

        assert len(result) == 2

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_with_unicode_filename(self, mock_download_core, temp_output_dir):
        """Test downloading files with unicode characters in names."""
        mock_download_core.return_value = b"<svg>content</svg>"

        titles = ["文件.svg", "Файл.svg"]
        result = download_commons_svgs(titles, temp_output_dir)

        assert len(result) == 2

    @patch("src.main_app.api_services.download_file_utils.download_commons_file_core")
    def test_download_timeout_handling(self, mock_download_core, temp_output_dir):
        """Test handling of request timeouts."""
        import requests

        mock_download_core.side_effect = requests.exceptions.Timeout("Timeout")

        titles = ["Timeout.svg"]
        result = download_commons_svgs(titles, temp_output_dir)

        assert len(result) == 0
