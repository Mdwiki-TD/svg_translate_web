"""Unit tests for toolforge_api_service.py."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import parse_qs, quote, quote_plus, urlsplit

import pytest
import requests
from src.main_app.api_services.clients.toolforge.toolforge_api_service import (
    API_ROUTES,
    API_URL,
    EXTERNAL_API_URL,
    REQUEST_TIMEOUT,
    TOKEN_ENV,
    ToolforgeApiService,
)

MODULE = "src.main_app.api_services.clients.toolforge.toolforge_api_service"

HTTP_METHODS = ["get", "post", "put", "patch", "delete"]


def _query(url: str) -> dict[str, list[str]]:
    """Return the decoded query string of a URL."""
    return parse_qs(urlsplit(url).query)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the environment variables read by the service."""
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    monkeypatch.delenv("TOOL_NAME", raising=False)


@pytest.fixture
def make_response() -> Callable[..., MagicMock]:
    """Return a factory that builds fake ``requests.Response`` objects."""

    def _factory(
        status_code: int = 200,
        json_data: Any = None,
        content: bytes = b"{}",
        text: str = "",
        json_error: bool = False,
    ) -> MagicMock:
        response = MagicMock(spec=requests.Response)
        response.status_code = status_code
        response.content = content
        response.text = text
        if json_error:
            response.json.side_effect = ValueError("no json")
        else:
            response.json.return_value = {} if json_data is None else json_data
        if status_code >= 400:
            response.raise_for_status.side_effect = requests.HTTPError(f"{status_code} error")
        return response

    return _factory


@pytest.fixture
def mock_http_client(make_response: Callable[..., MagicMock]) -> MagicMock:
    """Return a fake HttpClient whose request() answers with HTTP 200."""
    client = MagicMock()
    client.request.return_value = make_response()
    return client


@pytest.fixture
def make_service(mock_http_client: MagicMock) -> Callable[..., ToolforgeApiService]:
    """Return a factory that builds a service wired to the fake HttpClient."""

    def _factory(api_route: API_ROUTES = "jobs", **kwargs: Any) -> ToolforgeApiService:
        kwargs.setdefault("tool_name", "mytool")
        kwargs.setdefault("home_dir", "/home/tester")
        kwargs.setdefault("http_client", mock_http_client)
        return ToolforgeApiService(api_route, **kwargs)

    return _factory


class TestInit:
    """Mode selection and constructor defaults."""

    def test_without_token_runs_in_internal_mode(self, make_service) -> None:
        service = make_service()

        assert service.internal is True
        assert service.api_url == API_URL
        assert service.verify is False

    def test_with_token_runs_in_external_mode(self, make_service) -> None:
        service = make_service(token="secret")

        assert service.internal is False
        assert service.api_url == EXTERNAL_API_URL
        assert service.verify is True

    def test_token_is_read_from_environment(self, make_service, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(TOKEN_ENV, "env-token")

        service = make_service()

        assert service.token == "env-token"
        assert service.internal is False

    def test_explicit_token_wins_over_environment(self, make_service, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(TOKEN_ENV, "env-token")

        service = make_service(token="explicit")

        assert service.token == "explicit"

    def test_internal_flag_forces_internal_mode_even_with_token(self, make_service) -> None:
        service = make_service(token="secret", internal=True)

        assert service.internal is True
        assert service.api_url == API_URL
        assert service.verify is False

    def test_internal_false_forces_external_mode_without_token(self, make_service) -> None:
        service = make_service(internal=False)

        assert service.internal is False
        assert service.api_url == EXTERNAL_API_URL

    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [
            ({}, False),
            ({"verify": True}, True),
            ({"token": "secret"}, True),
            ({"token": "secret", "verify": False}, False),
        ],
    )
    def test_verify_default_depends_on_mode_and_can_be_overridden(
        self, make_service, kwargs: dict[str, Any], expected: bool
    ) -> None:
        assert make_service(**kwargs).verify is expected

    def test_tool_name_argument(self, make_service) -> None:
        assert make_service(tool_name="custom").tool_name == "custom"

    def test_tool_name_falls_back_to_environment(self, make_service, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("TOOL_NAME", "envtool")

        assert make_service(tool_name=None).tool_name == "envtool"

    def test_tool_name_falls_back_to_tool_name(self, make_service) -> None:
        assert make_service(tool_name=None).tool_name == "tool_name"

    def test_home_dir_defaults_to_user_home(self, make_service) -> None:
        assert make_service(home_dir=None).home_dir == str(Path.home())

    def test_timeout_default_and_override(self, make_service) -> None:
        assert make_service().timeout == REQUEST_TIMEOUT
        assert make_service(timeout=3).timeout == 3

    def test_api_route_is_stored(self, make_service) -> None:
        assert make_service("builds").api_route == "builds"

    def test_default_http_client_is_created(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_client_class = MagicMock()
        monkeypatch.setattr(f"{MODULE}.HttpClient", fake_client_class)

        service = ToolforgeApiService("jobs", tool_name="mytool", home_dir="/home/tester")

        assert service.http_client is fake_client_class.return_value


class TestClientCert:
    """Paths of the client certificate."""

    def test_returns_cert_and_key_paths(self, make_service) -> None:
        service = make_service(home_dir="/data/project")

        assert service.client_cert == (
            "/data/project/.toolskube/client.crt",
            "/data/project/.toolskube/client.key",
        )


class TestBuildUrl:
    """URL building and token handling."""

    def test_internal_url_has_no_query(self, make_service) -> None:
        service = make_service()

        assert service.build_url("/jobs/v1/healthz") == f"{API_URL}/jobs/v1/healthz"

    def test_external_url_appends_token(self, make_service) -> None:
        service = make_service(token="secret")

        assert service.build_url("/jobs/v1/healthz") == f"{EXTERNAL_API_URL}/jobs/v1/healthz?token=secret"

    def test_params_are_added_to_the_query(self, make_service) -> None:
        service = make_service()

        url = service.build_url("/logs", params={"lines": 10, "name": "job"})

        assert _query(url) == {"lines": ["10"], "name": ["job"]}

    def test_none_params_are_skipped(self, make_service) -> None:
        service = make_service()

        url = service.build_url("/logs", params={"lines": None, "name": "job"})

        assert _query(url) == {"name": ["job"]}

    def test_all_none_params_leave_no_query(self, make_service) -> None:
        service = make_service()

        assert service.build_url("/logs", params={"lines": None}) == f"{API_URL}/logs"

    @pytest.mark.parametrize(("value", "expected"), [(True, "true"), (False, "false")])
    def test_bool_params_are_lowercase(self, make_service, value: bool, expected: str) -> None:
        service = make_service()

        url = service.build_url("/logs", params={"follow": value})

        assert _query(url) == {"follow": [expected]}

    def test_params_and_token_are_combined(self, make_service) -> None:
        service = make_service(token="secret")

        url = service.build_url("/logs", params={"lines": 5})

        assert _query(url) == {"lines": ["5"], "token": ["secret"]}

    def test_token_is_url_encoded(self, make_service) -> None:
        service = make_service(token="a b/c+d&e")

        url = service.build_url("/jobs")

        assert "a b" not in url
        assert _query(url)["token"] == ["a b/c+d&e"]

    def test_token_is_not_added_in_internal_mode_even_with_token(self, make_service) -> None:
        service = make_service(token="secret", internal=True)

        assert "token" not in service.build_url("/jobs")


class TestRedact:
    """Hiding the token in error messages."""

    def test_text_is_unchanged_without_token(self, make_service) -> None:
        service = make_service()

        assert service.redact("nothing to hide") == "nothing to hide"

    def test_token_is_replaced(self, make_service) -> None:
        service = make_service(token="secret")

        assert service.redact("url?token=secret") == "url?token=***"

    def test_every_occurrence_is_replaced(self, make_service) -> None:
        service = make_service(token="secret")

        assert service.redact("secret and secret") == "*** and ***"

    @pytest.mark.parametrize("token", ["secret", "a b", "a/b+c=d", "x&y?z"])
    def test_every_url_encoding_is_replaced(self, make_service, token: str) -> None:
        service = make_service(token=token)

        for variant in (token, quote(token), quote(token, safe=""), quote_plus(token)):
            message = f"500 for url: https://host/jobs?token={variant}"

            assert service.redact(message) == "500 for url: https://host/jobs?token=***"

    def test_unrelated_text_is_kept(self, make_service) -> None:
        service = make_service(token="secret")

        assert service.redact("500 Server Error for url") == "500 Server Error for url"


class TestRequest:
    """Low-level request sending."""

    def test_internal_request_sends_cert_and_skips_verification(self, make_service, mock_http_client) -> None:
        service = make_service()

        service.request("GET", "/jobs/v1/healthz")

        mock_http_client.request.assert_called_once_with(
            method="GET",
            url=f"{API_URL}/jobs/v1/healthz",
            verify=False,
            timeout=REQUEST_TIMEOUT,
            cert=("/home/tester/.toolskube/client.crt", "/home/tester/.toolskube/client.key"),
        )

    def test_external_request_sends_token_and_no_cert(self, make_service, mock_http_client) -> None:
        service = make_service(token="secret")

        service.request("GET", "/jobs/v1/healthz")

        mock_http_client.request.assert_called_once_with(
            method="GET",
            url=f"{EXTERNAL_API_URL}/jobs/v1/healthz?token=secret",
            verify=True,
            timeout=REQUEST_TIMEOUT,
        )

    def test_custom_timeout_is_used(self, make_service, mock_http_client) -> None:
        service = make_service(timeout=2)

        service.request("GET", "/jobs")

        assert mock_http_client.request.call_args.kwargs["timeout"] == 2

    @pytest.mark.parametrize("method", HTTP_METHODS)
    def test_http_verb_is_dispatched_to_matching_client_method(
        self, make_service, mock_http_client, method: str
    ) -> None:
        service = make_service()

        service.request(method.upper(), "/jobs")

        mock_http_client.request.assert_called_once()
        assert mock_http_client.request.call_args.kwargs["method"] == method.upper()

    def test_json_body_is_sent(self, make_service, mock_http_client) -> None:
        service = make_service()

        service.request("POST", "/jobs", json={"name": "update"})

        assert mock_http_client.request.call_args.kwargs["json"] == {"name": "update"}

    def test_empty_json_body_is_still_sent(self, make_service, mock_http_client) -> None:
        service = make_service()

        service.request("POST", "/jobs", json={})

        assert mock_http_client.request.call_args.kwargs["json"] == {}

    def test_json_is_omitted_when_none(self, make_service, mock_http_client) -> None:
        service = make_service()

        service.request("POST", "/jobs")

        assert "json" not in mock_http_client.request.call_args.kwargs

    def test_params_are_added_to_the_url(self, make_service, mock_http_client) -> None:
        service = make_service()

        service.request("GET", "/logs", params={"lines": 7})

        assert _query(mock_http_client.request.call_args.kwargs["url"]) == {"lines": ["7"]}

    def test_returns_the_raw_response(self, make_service, mock_http_client, make_response) -> None:
        expected = make_response(json_data={"ok": True})
        mock_http_client.request.return_value = expected
        service = make_service()

        assert service.request("GET", "/jobs") is expected

    def test_external_mode_without_token_raises_before_sending(self, make_service, mock_http_client) -> None:
        service = make_service(internal=False)

        with pytest.raises(ValueError, match=TOKEN_ENV):
            service.request("GET", "/jobs")

        mock_http_client.request.assert_not_called()

    def test_http_error_raises_by_default(self, make_service, mock_http_client, make_response) -> None:
        mock_http_client.request.return_value = make_response(status_code=500)
        service = make_service()

        with pytest.raises(requests.HTTPError):
            service.request("GET", "/jobs")

    def test_check_false_returns_error_response(self, make_service, mock_http_client, make_response) -> None:
        error_response = make_response(status_code=404)
        mock_http_client.request.return_value = error_response
        service = make_service()

        result = service.request("GET", "/jobs", check=False)

        assert result is error_response
        error_response.raise_for_status.assert_not_called()


class TestPayload:
    """Decoding of response bodies."""

    def test_empty_body_returns_empty_dict(self, make_response) -> None:
        response = make_response(content=b"")

        assert ToolforgeApiService._payload(response) == {}
        response.json.assert_not_called()

    def test_json_body_is_decoded(self, make_response) -> None:
        response = make_response(json_data={"jobs": []})

        assert ToolforgeApiService._payload(response) == {"jobs": []}

    def test_json_list_is_returned_as_is(self, make_response) -> None:
        response = make_response(json_data=[1, 2])

        assert ToolforgeApiService._payload(response) == [1, 2]

    def test_invalid_json_falls_back_to_text(self, make_response) -> None:
        response = make_response(content=b"plain", text="plain", json_error=True)

        assert ToolforgeApiService._payload(response) == "plain"


class TestToolPath:
    """Tool-scoped paths."""

    def test_default_path(self, make_service) -> None:
        assert make_service()._tool_path() == "/jobs/v1/tool/mytool"

    def test_path_with_suffix(self, make_service) -> None:
        assert make_service()._tool_path("/jobs") == "/jobs/v1/tool/mytool/jobs"

    def test_route_is_part_of_the_path(self, make_service) -> None:
        assert make_service("builds")._tool_path("/quotas") == "/builds/v1/tool/mytool/quotas"

    def test_tool_name_is_quoted(self, make_service) -> None:
        service = make_service(tool_name="my tool/x")

        assert service._tool_path("/jobs") == "/jobs/v1/tool/my%20tool%2Fx/jobs"


class TestHealthcheck:
    """GET /<route>/v1/healthz."""

    @pytest.mark.parametrize("route", ["builds", "components", "envvars", "jobs", "logs"])
    def test_requests_versioned_healthz_path(self, make_service, mock_http_client, route: str) -> None:
        service = make_service(route)

        service.healthcheck()

        assert mock_http_client.request.call_args.kwargs["url"] == f"{API_URL}/{route}/v1/healthz"

    def test_returns_decoded_payload(
        self,
        make_service,
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(json_data={"status": "ok"})
        service = make_service()

        assert service.healthcheck() == {"status": "ok"}

    def test_http_error_is_raised(self, make_service, mock_http_client, make_response) -> None:
        mock_http_client.request.return_value = make_response(status_code=503)
        service = make_service()

        with pytest.raises(requests.HTTPError):
            service.healthcheck()


class TestMetrics:
    """GET /<route>/v1/metrics (or /<route>/metrics)."""

    @pytest.mark.parametrize("route", ["builds", "envvars", "jobs"])
    def test_versioned_metrics_path(self, make_service, mock_http_client, route: str) -> None:
        service = make_service(route)

        service.metrics()

        assert mock_http_client.request.call_args.kwargs["url"] == f"{API_URL}/{route}/v1/metrics"

    @pytest.mark.parametrize("route", ["components", "logs"])
    def test_unversioned_metrics_path(self, make_service, mock_http_client, route: str) -> None:
        service = make_service(route)

        service.metrics()

        assert mock_http_client.request.call_args.kwargs["url"] == f"{API_URL}/{route}/metrics"

    def test_returns_plain_text(self, make_service, mock_http_client, make_response) -> None:
        mock_http_client.request.return_value = make_response(content=b"# HELP x", text="# HELP x")
        service = make_service()

        assert service.metrics() == "# HELP x"

    def test_external_metrics_request_carries_token(self, make_service, mock_http_client) -> None:
        service = make_service(token="secret")

        service.metrics()

        assert mock_http_client.request.call_args.kwargs["url"] == f"{EXTERNAL_API_URL}/jobs/v1/metrics?token=secret"
