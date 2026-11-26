"""Simple tests for HttpClient."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests
import src.main_app.api_services.clients.http_client as hc
from src.main_app.api_services.clients.http_client import HttpClient


def make_response(status: int = 200, text: str = "ok") -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    resp.text = text
    return resp


@pytest.fixture
def mock_request(monkeypatch):
    """Replace requests.request inside the module and return the mock."""
    mock = MagicMock(return_value=make_response())
    monkeypatch.setattr(hc.requests, "request", mock)
    return mock


@pytest.fixture
def client() -> HttpClient:
    return HttpClient(default_timeout=10.0, user_agent="TestAgent/1.0")


# ----------------------------------------------------------------------
# User-Agent / headers
# ----------------------------------------------------------------------
def test_custom_user_agent_is_used(client):
    assert client.user_agent == "TestAgent/1.0"


def test_prepare_headers_adds_user_agent(client):
    assert client._prepare_headers(None) == {"User-Agent": "TestAgent/1.0"}


def test_prepare_headers_does_not_override_existing_user_agent(client):
    headers = client._prepare_headers({"user-agent": "Mine"})
    assert headers == {"user-agent": "Mine"}


def test_prepare_headers_does_not_mutate_input(client):
    original = {"X-Test": "1"}
    client._prepare_headers(original)
    assert original == {"X-Test": "1"}


# ----------------------------------------------------------------------
# get / post / request
# ----------------------------------------------------------------------
def test_get_sends_expected_arguments(client, mock_request):
    client.get("https://example.com", params={"a": 1})

    kwargs = mock_request.call_args.kwargs
    assert kwargs["method"] == "GET"
    assert kwargs["url"] == "https://example.com"
    assert kwargs["params"] == {"a": 1}
    assert kwargs["timeout"] == 10.0
    assert kwargs["headers"]["User-Agent"] == "TestAgent/1.0"


def test_get_timeout_override(client, mock_request):
    client.get("https://example.com", timeout=3.5)
    assert mock_request.call_args.kwargs["timeout"] == 3.5


def test_post_sends_json_and_data(client, mock_request):
    client.post("https://example.com", json={"k": "v"}, data={"d": 1})

    kwargs = mock_request.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["json"] == {"k": "v"}
    assert kwargs["data"] == {"d": 1}


def test_request_uppercases_method_and_maps_json_data(client, mock_request):
    client.request("put", "https://example.com", json_data={"x": 1})

    kwargs = mock_request.call_args.kwargs
    assert kwargs["method"] == "PUT"
    assert kwargs["json"] == {"x": 1}


def test_get_returns_response_object(client, mock_request):
    resp = make_response(200, "hello")
    mock_request.return_value = resp
    assert client.get("https://example.com") is resp


# ----------------------------------------------------------------------
# safe_request
# ----------------------------------------------------------------------
def test_safe_request_success(client, mock_request):
    mock_request.return_value = make_response(200, "body")

    result = client.safe_request("https://example.com")

    assert result == {"output": "body", "error": "", "error_code": "", "http_code": 200}


def test_safe_request_timeout(client, mock_request):
    mock_request.side_effect = requests.Timeout()

    result = client.safe_request("https://example.com")

    assert result["error_code"] == "TIMEOUT"
    assert result["error"] == "Request timed out"
    assert result["output"] == ""


def test_safe_request_generic_exception(client, mock_request):
    mock_request.side_effect = requests.ConnectionError("boom")

    result = client.safe_request("https://example.com")

    assert result["error_code"] == "REQUEST_ERROR"
    assert "boom" in result["error"]


def test_safe_request_http_error(client, mock_request):
    mock_request.return_value = make_response(404, "not found")

    result = client.safe_request("https://example.com")

    assert result["error"] == "HTTP_ERROR"
    assert result["error_code"] == "404"
    assert result["http_code"] == 404
    assert result["output"] == ""


def test_safe_request_detects_cloudflare(client, mock_request):
    mock_request.return_value = make_response(403, "<title>Just a moment...</title>")

    result = client.safe_request("https://example.com")

    assert result["error"] == "CLOUDFLARE_PROTECTION"
    assert result["error_code"] == "403"
    assert result["output"] == ""


def test_safe_request_uses_default_15s_timeout(client, mock_request):
    client.safe_request("https://example.com")
    assert mock_request.call_args.kwargs["timeout"] == 15.0
