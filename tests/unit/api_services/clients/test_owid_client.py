"""Tests for src.main_app.api_services.clients.owid_client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
from src.main_app.api_services.clients.owid_client import OwidClient


@dataclass
class _FakeResponse:
    """Minimal HTTP response double for OwidClient tests."""

    status_code: int | None
    payload: dict[str, Any] | None = None
    json_error: Exception | None = None

    def json(self) -> dict[str, Any]:
        if self.json_error is not None:
            raise self.json_error
        return self.payload or {}


class _FakeHttpClient:
    """Minimal HTTP client double exposing `.get(url, timeout=...)`."""

    def __init__(
        self,
        response: _FakeResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error
        self.calls: list[tuple[str, float]] = []

    def get(self, url: str, timeout: float = 15) -> _FakeResponse:
        self.calls.append((url, timeout))
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


@pytest.fixture
def make_client():
    """Factory fixture creating an OwidClient wired to a fake HTTP client."""

    def _factory(
        response: _FakeResponse | None = None,
        error: Exception | None = None,
        timeout: float = 15,
    ) -> tuple[OwidClient, _FakeHttpClient]:
        fake_http = _FakeHttpClient(response=response, error=error)
        client = OwidClient(http_client=fake_http, timeout=timeout)
        return client, fake_http

    return _factory


class TestOwidClientInit:
    """Tests for OwidClient initialization."""

    def test_uses_injected_http_client(self, make_client):
        """Test that a custom http_client instance is stored directly."""
        client, fake_http = make_client(response=_FakeResponse(status_code=200))
        assert client.http_client is fake_http

    def test_creates_default_http_client_when_none_provided(self, monkeypatch):
        """Test that a default HttpClient(use_session=True) is created when omitted."""
        mock_http_cls = MagicMock()
        monkeypatch.setattr(
            "src.main_app.api_services.clients.owid_client.HttpClient",
            mock_http_cls,
        )

        client = OwidClient()

        mock_http_cls.assert_called_once_with(use_session=True, default_timeout=15)
        assert client.http_client is mock_http_cls.return_value


class TestOwidClientFetchGrapherMetadataRaw:
    """Tests for OwidClient.fetch_grapher_metadata_raw."""

    def test_successful_fetch_returns_parsed_json(self, make_client):
        """Test that a 200 response returns parsed JSON and status code."""
        payload = {"name": "chart", "data": [1, 2, 3]}
        client, fake_http = make_client(response=_FakeResponse(status_code=200, payload=payload))

        result = client.fetch_grapher_metadata_raw("test-slug")

        assert result.data == payload
        assert result.status_code == 200
        assert fake_http.calls == [("https://ourworldindata.org/grapher/test-slug.metadata.json", 15)]

    def test_non_200_status_returns_none_data(self, make_client):
        """Test that a non-200 response returns None data while preserving status code."""
        client, _ = make_client(response=_FakeResponse(status_code=404, payload={"error": "Not Found"}))

        result = client.fetch_grapher_metadata_raw("missing-slug")

        assert result.data is None
        assert result.status_code == 404

    def test_network_error_returns_none_and_none_status(self, make_client):
        """Test that a connection error returns None data and None status code."""
        client, _ = make_client(error=requests.ConnectionError("Connection refused"))

        result = client.fetch_grapher_metadata_raw("bad-host")

        assert result.data is None
        assert result.status_code is None

    def test_invalid_json_response_returns_none(self, make_client):
        """Test that a non-JSON response returns None data and None status code."""
        client, _ = make_client(response=_FakeResponse(status_code=200, json_error=ValueError("Expecting value")))

        result = client.fetch_grapher_metadata_raw("bad-json")

        assert result.data is None
        assert result.status_code is None


class TestOwidClientFetchIndicatorsMetadata:
    """Tests for OwidClient.fetch_indicators_metadata."""

    def test_successful_fetch_returns_parsed_json(self, make_client):
        """Test that a 200 response returns parsed indicator metadata."""
        payload = {"id": 123, "name": "Population"}
        client, fake_http = make_client(response=_FakeResponse(status_code=200, payload=payload))

        result = client.fetch_indicators_metadata(123)

        assert result.data == payload
        assert result.status_code == 200
        assert fake_http.calls == [("https://api.ourworldindata.org/v1/indicators/123.metadata.json", 15)]

    def test_non_200_status_returns_none_data(self, make_client):
        """Test that a 500 response returns None data and status code 500."""
        client, _ = make_client(response=_FakeResponse(status_code=500, payload={"error": "Server Error"}))

        result = client.fetch_indicators_metadata(999)

        assert result.data is None
        assert result.status_code == 500

    def test_network_error_returns_none_and_none_status(self, make_client):
        """Test that a connection error returns None data and None status code."""
        client, _ = make_client(error=requests.ConnectionError("Timeout"))

        result = client.fetch_indicators_metadata(456)

        assert result.data is None
        assert result.status_code is None
