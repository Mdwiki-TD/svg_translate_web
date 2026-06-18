"""Tests for src.main_app.api_services.clients.owid_client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests

from src.main_app.api_services.clients.owid_client import (
    _build_session,
    _thread_local,
    fetch_grapher_metadata,
    fetch_indicators_metadata,
    METADATA_URL,
    INDICATORS_METADATA_URL,
    REQUEST_TIMEOUT,
)


class TestBuildSession:
    """Tests for _build_session function."""

    @pytest.fixture(autouse=True)
    def _clean_thread_local(self):
        """Remove any cached session before and after each test."""
        if hasattr(_thread_local, "session"):
            del _thread_local.session
        yield
        if hasattr(_thread_local, "session"):
            del _thread_local.session

    def _mock_settings(self, monkeypatch, user_agent: str = "TestBot/1.0"):
        """Replace owid_client.settings with a mock to avoid frozen dataclass."""
        mock_settings = MagicMock()
        mock_settings.other.user_agent = user_agent
        monkeypatch.setattr(
            "src.main_app.api_services.clients.owid_client.settings",
            mock_settings,
        )

    def test_creates_session_on_first_call(self, monkeypatch):
        """Test that a requests Session is created on first call to _build_session."""
        self._mock_settings(monkeypatch)
        session = _build_session()
        assert isinstance(session, requests.Session)

    def test_reuses_existing_session_on_subsequent_calls(self, monkeypatch):
        """Test that the same session is returned on subsequent calls."""
        self._mock_settings(monkeypatch)
        session1 = _build_session()
        session2 = _build_session()
        assert session1 is session2

    def test_sets_user_agent_from_settings(self, monkeypatch):
        """Test that the User-Agent header is taken from settings.other.user_agent."""
        self._mock_settings(monkeypatch, user_agent="CustomBot/2.0")
        session = _build_session()
        assert session.headers["User-Agent"] == "CustomBot/2.0"


class TestFetchGrapherMetadata:
    """Tests for fetch_grapher_metadata function."""

    @staticmethod
    def _mock_session(monkeypatch) -> MagicMock:
        """Replace _build_session with a mock and return the mock session."""
        mock_session = MagicMock()
        monkeypatch.setattr(
            "src.main_app.api_services.clients.owid_client._build_session",
            lambda: mock_session,
        )
        return mock_session

    def test_successful_fetch_returns_parsed_json(self, monkeypatch):
        """Test that a successful response returns the parsed dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "chart", "data": [1, 2, 3]}
        mock_session = self._mock_session(monkeypatch)
        mock_session.get.return_value = mock_response

        result = fetch_grapher_metadata("test-slug")

        assert result == {"name": "chart", "data": [1, 2, 3]}
        mock_session.get.assert_called_once_with(
            "https://ourworldindata.org/grapher/test-slug.metadata.json",
            timeout=15,
        )

    def test_http_error_returns_none(self, monkeypatch):
        """Test that an HTTP error (raise_for_status) returns None."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_session = self._mock_session(monkeypatch)
        mock_session.get.return_value = mock_response

        result = fetch_grapher_metadata("missing-slug")

        assert result is None

    def test_network_error_returns_none(self, monkeypatch):
        """Test that a connection error returns None."""
        mock_session = self._mock_session(monkeypatch)
        mock_session.get.side_effect = requests.ConnectionError("Connection refused")

        result = fetch_grapher_metadata("bad-host")

        assert result is None

    def test_invalid_json_response_returns_none(self, monkeypatch):
        """Test that a non-JSON response returns None."""
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Expecting value")
        mock_session = self._mock_session(monkeypatch)
        mock_session.get.return_value = mock_response

        result = fetch_grapher_metadata("bad-json")

        assert result is None


class TestFetchIndicatorsMetadata:
    """Tests for fetch_indicators_metadata function."""

    @staticmethod
    def _mock_session(monkeypatch) -> MagicMock:
        """Replace _build_session with a mock and return the mock session."""
        mock_session = MagicMock()
        monkeypatch.setattr(
            "src.main_app.api_services.clients.owid_client._build_session",
            lambda: mock_session,
        )
        return mock_session

    def test_successful_fetch_returns_parsed_json(self, monkeypatch):
        """Test that a successful response returns the parsed dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 123, "name": "Population"}
        mock_session = self._mock_session(monkeypatch)
        mock_session.get.return_value = mock_response

        result = fetch_indicators_metadata(123)

        assert result == {"id": 123, "name": "Population"}
        mock_session.get.assert_called_once_with(
            "https://api.ourworldindata.org/v1/indicators/123.metadata.json",
            timeout=15,
        )

    def test_http_error_returns_none(self, monkeypatch):
        """Test that an HTTP error returns None."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_session = self._mock_session(monkeypatch)
        mock_session.get.return_value = mock_response

        result = fetch_indicators_metadata(999)

        assert result is None

    def test_network_error_returns_none(self, monkeypatch):
        """Test that a connection error returns None."""
        mock_session = self._mock_session(monkeypatch)
        mock_session.get.side_effect = requests.ConnectionError("Timeout")

        result = fetch_indicators_metadata(456)

        assert result is None
