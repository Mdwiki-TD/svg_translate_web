"""Tests for src.main_app.api_services.clients.commons_client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.main_app.api_services.clients.commons_client import (
    BASE_COMMONS_URL,
    create_commons_session,
    download_commons_file_core,
)


class TestCreateCommonsSession:
    """Tests for create_commons_session function."""

    def test_creates_session(self):
        """Test that a requests Session is created."""
        session = create_commons_session()
        assert isinstance(session, requests.Session)

    def test_default_user_agent(self):
        """Test default User-Agent header."""
        session = create_commons_session()
        assert session.headers["User-Agent"] == "SVGTranslateBot/1.0"

    def test_custom_user_agent(self):
        """Test custom User-Agent header."""
        session = create_commons_session("MyBot/2.0")
        assert session.headers["User-Agent"] == "MyBot/2.0"


class TestDownloadCommonsFileCore:
    """Tests for download_commons_file_core function."""

    def test_successful_download(self):
        """Test successful file download."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        session.get.return_value = mock_response

        result = download_commons_file_core("Test.svg", session)

        assert result == b"<svg>test</svg>"
        expected_url = f"{BASE_COMMONS_URL}Test.svg"
        session.get.assert_called_once_with(expected_url, timeout=60, allow_redirects=True)

    def test_spaces_converted_to_underscores(self):
        """Test that spaces in filename are converted to underscores."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"content"
        session.get.return_value = mock_response

        download_commons_file_core("My File.svg", session)

        expected_url = f"{BASE_COMMONS_URL}My_File.svg"
        session.get.assert_called_once_with(expected_url, timeout=60, allow_redirects=True)

    def test_custom_timeout(self):
        """Test custom timeout is passed through."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"content"
        session.get.return_value = mock_response

        download_commons_file_core("Test.svg", session, timeout=30)

        session.get.assert_called_once()
        call_kwargs = session.get.call_args[1]
        assert call_kwargs["timeout"] == 30

    def test_http_error_raises_exception(self):
        """Test that HTTP errors raise exceptions."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        session.get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            download_commons_file_core("Missing.svg", session)

    def test_network_error_raises_exception(self):
        """Test that network errors raise exceptions."""
        session = MagicMock()
        session.get.side_effect = requests.ConnectionError("Connection refused")

        with pytest.raises(requests.ConnectionError):
            download_commons_file_core("Test.svg", session)

    def test_timeout_error_raises_exception(self):
        """Test that timeouts raise exceptions."""
        session = MagicMock()
        session.get.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(requests.Timeout):
            download_commons_file_core("Test.svg", session)

    def test_filename_is_url_encoded(self):
        """Test that special characters in filename are URL encoded."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"content"
        session.get.return_value = mock_response

        download_commons_file_core("File (with parens).svg", session)

        call_args = session.get.call_args[0][0]
        assert "%28" in call_args
        assert "%29" in call_args
