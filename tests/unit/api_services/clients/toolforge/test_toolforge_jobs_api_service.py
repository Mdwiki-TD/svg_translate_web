"""Unit tests for toolforge_jobs_api_service.py."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
from src.main_app.api_services.clients.toolforge.toolforge_api_service import (
    API_URL,
    EXTERNAL_API_URL,
    REQUEST_TIMEOUT,
    TOKEN_ENV,
)
from src.main_app.api_services.clients.toolforge.toolforge_jobs_api_service import (
    ToolforgeApiError,
    ToolforgeJobsService,
)
from src.main_app.api_services.clients.toolforge.toolforge_jobs_types import (
    ImagesResponse,
    JobListResponse,
    JobResponse,
    MessagesResponse,
    QuotaResponse,
    ResponseMessages,
    UpdateResponse,
)

HTTP_METHODS = ["get", "post", "put", "patch", "delete"]

BASE = f"{API_URL}/jobs/v1/tool/mytool"


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
def make_service(mock_http_client: MagicMock) -> Callable[..., ToolforgeJobsService]:
    """Return a factory that builds a jobs service wired to the fake HttpClient."""

    def _factory(**kwargs: Any) -> ToolforgeJobsService:
        kwargs.setdefault("tool_name", "mytool")
        kwargs.setdefault("home_dir", "/home/tester")
        kwargs.setdefault("http_client", mock_http_client)
        return ToolforgeJobsService(**kwargs)

    return _factory


class TestInit:
    """Constructor behavior of the jobs client."""

    def test_route_is_jobs(
        self,
        make_service: Callable[..., ToolforgeJobsService],
    ) -> None:
        assert make_service().api.api_route == "jobs"

    def test_default_mode_is_internal(
        self,
        make_service: Callable[..., ToolforgeJobsService],
    ) -> None:
        service = make_service()

        assert service.api.internal is True
        assert service.api.api_url == API_URL

    def test_token_switches_to_external_mode(
        self,
        make_service: Callable[..., ToolforgeJobsService],
    ) -> None:
        service = make_service(token="secret")

        assert service.api.internal is False
        assert service.api.api_url == EXTERNAL_API_URL

    def test_arguments_are_forwarded_to_the_base_class(
        self,
        mock_http_client,
    ) -> None:
        service = ToolforgeJobsService(
            tool_name="custom",
            home_dir="/data",
            verify=True,
            timeout=4,
            http_client=mock_http_client,
            token="secret",
            internal=True,
        )

        assert service.api.tool_name == "custom"
        assert service.api.home_dir == "/data"
        assert service.api.verify is True
        assert service.api.timeout == 4
        assert service.api.http_client is mock_http_client
        assert service.api.token == "secret"
        assert service.api.internal is True

    def test_timeout_default(
        self,
        make_service: Callable[..., ToolforgeJobsService],
    ) -> None:
        assert make_service().api.timeout == REQUEST_TIMEOUT


class TestJobPath:
    """Sub-path of a single job."""

    def test_integer_id(
        self,
        make_service: Callable[..., ToolforgeJobsService],
    ) -> None:
        assert make_service()._job_path(5) == "/jobs/5"

    def test_string_id(
        self,
        make_service: Callable[..., ToolforgeJobsService],
    ) -> None:
        assert make_service()._job_path("update") == "/jobs/update"

    def test_id_is_quoted(
        self,
        make_service: Callable[..., ToolforgeJobsService],
    ) -> None:
        assert make_service()._job_path("a b/c") == "/jobs/a%20b%2Fc"


class TestReadEndpoints:
    """GET endpoints."""

    @pytest.mark.parametrize(
        ("method_name", "args", "expected_path"),
        [
            ("images", (), "/images"),
            ("quotas", (), "/quotas"),
            ("list_jobs", (), "/jobs"),
            ("show_job", ("update",), "/jobs/update"),
            ("get_logs", ("update",), "/jobs/update/logs"),
        ],
    )
    def test_request_url_and_method(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        method_name: str,
        args: tuple,
        expected_path: str,
    ) -> None:
        service = make_service()

        getattr(service, method_name)(*args)

        mock_http_client.request.assert_called_once()
        assert mock_http_client.request.call_args.kwargs["method"] == "GET"
        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}{expected_path}"

    @pytest.mark.parametrize(
        ("method_name", "args", "expected_type"),
        [
            ("images", (), ImagesResponse),
            ("quotas", (), QuotaResponse),
            ("list_jobs", (), JobListResponse),
            ("show_job", (1,), JobResponse),
        ],
    )
    def test_returns_loaded_dataclass(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
        method_name: str,
        args: tuple,
        expected_type: type,
    ) -> None:
        mock_http_client.request.return_value = make_response(json_data={"messages": {"info": ["ok"]}})
        service = make_service()

        result = getattr(service, method_name)(*args)

        assert isinstance(result, expected_type)
        assert result.messages is not None
        assert result.messages.info == ["ok"]

    def test_show_job_quotes_the_id(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.show_job("my job")

        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}/jobs/my%20job"

    def test_list_jobs_returns_the_api_payload(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        payload = {
            "jobs": [{"name": "update"}],
            "messages": {"info": [], "warning": [], "error": []},
        }
        mock_http_client.request.return_value = make_response(json_data=payload)
        service = make_service()

        jobs = service.list_jobs()

        assert jobs.messages is not None
        assert jobs.messages.to_json() == payload["messages"]
        assert jobs.jobs is not None
        assert jobs.jobs[0].name == "update"

    @pytest.mark.parametrize(
        ("method_name", "args"),
        [("images", ()), ("quotas", ()), ("list_jobs", ()), ("show_job", ("update",))],
    )
    def test_non_json_body_raises_value_error(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
        method_name: str,
        args: tuple,
    ) -> None:
        mock_http_client.request.return_value = make_response(content=b"oops", text="oops", json_error=True)
        service = make_service()

        with pytest.raises(ValueError):
            getattr(service, method_name)(*args)


class TestListJobsIncludeUnset:
    """The only query parameter of GET /jobs."""

    def test_no_query_string_by_default(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.list_jobs()

        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}/jobs"

    @pytest.mark.parametrize(("value", "expected"), [(True, "true"), (False, "false")])
    def test_include_unset_is_sent_lowercase(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        value: bool,
        expected: str,
    ) -> None:
        service = make_service()

        service.list_jobs(include_unset=value)

        assert _query(mock_http_client.request.call_args.kwargs["url"]) == {"include_unset": [expected]}


class TestGetLogs:
    """The logs endpoint returns text/plain and takes no query parameters."""

    def test_returns_the_plain_text(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(content=b"line 1\nline 2", text="line 1\nline 2")
        service = make_service()

        assert service.get_logs("update") == "line 1\nline 2"

    def test_text_that_looks_like_json_is_not_decoded(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        response = make_response(content=b"123", text="123", json_data=123)
        mock_http_client.request.return_value = response
        service = make_service()

        assert service.get_logs("update") == "123"
        response.json.assert_not_called()

    def test_empty_logs_return_empty_string(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(content=b"", text="")
        service = make_service()

        assert service.get_logs("update") == ""

    def test_no_query_string_is_sent(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.get_logs("update")

        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}/jobs/update/logs"

    def test_http_error_is_raised(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(status_code=404)
        service = make_service()

        with pytest.raises(requests.HTTPError):
            service.get_logs("missing")


class TestWriteEndpoints:
    """POST, PATCH and DELETE endpoints."""

    def test_create_job_posts_the_data(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()
        data = {"name": "update", "imagename": "python3.13", "cmd": "./run.sh"}

        service.create_job(data)

        mock_http_client.request.assert_called_once()
        assert mock_http_client.request.call_args.kwargs["method"] == "POST"
        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}/jobs"
        assert mock_http_client.request.call_args.kwargs["json"] == data

    def test_update_job_patches_the_data(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()
        data = {"name": "update", "cpu": "0.2"}

        service.update_job(data)

        mock_http_client.request.assert_called_once()
        assert mock_http_client.request.call_args.kwargs["method"] == "PATCH"
        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}/jobs"
        assert mock_http_client.request.call_args.kwargs["json"] == data

    def test_flush_jobs_deletes_the_collection(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.flush_jobs()

        mock_http_client.request.assert_called_once()
        assert mock_http_client.request.call_args.kwargs["method"] == "DELETE"
        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}/jobs"
        assert "json" not in mock_http_client.request.call_args.kwargs

    def test_delete_job_deletes_one_job(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.delete_job("update")

        mock_http_client.request.assert_called_once()
        assert mock_http_client.request.call_args.kwargs["method"] == "DELETE"
        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}/jobs/update"

    def test_restart_job_posts_to_the_restart_path(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.restart_job("update")

        mock_http_client.request.assert_called_once()
        assert mock_http_client.request.call_args.kwargs["method"] == "POST"
        assert mock_http_client.request.call_args.kwargs["url"] == f"{BASE}/jobs/update/restart"
        assert "json" not in mock_http_client.request.call_args.kwargs

    @pytest.mark.parametrize(
        ("method_name", "args", "expected_type"),
        [
            ("create_job", ({"name": "x"},), JobResponse),
            ("update_job", ({"name": "x"},), UpdateResponse),
            ("flush_jobs", (), MessagesResponse),
            ("delete_job", ("x",), MessagesResponse),
            ("restart_job", ("x",), MessagesResponse),
        ],
    )
    def test_returns_loaded_dataclass(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
        method_name: str,
        args: tuple,
        expected_type: type,
    ) -> None:
        mock_http_client.request.return_value = make_response(json_data={"messages": {"info": ["ok"]}})
        service = make_service()

        result = getattr(service, method_name)(*args)

        assert isinstance(result, expected_type)
        assert result.messages is not None
        assert result.messages.info == ["ok"]

    @pytest.mark.parametrize(
        ("method_name", "args", "client_method"),
        [
            ("create_job", ({"name": "x"},), "POST"),
            ("update_job", ({"name": "x"},), "PATCH"),
            ("flush_jobs", (), "DELETE"),
            ("delete_job", ("x",), "DELETE"),
            ("restart_job", ("x",), "POST"),
        ],
    )
    def test_http_error_is_raised(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
        method_name: str,
        args: tuple,
        client_method: str,
    ) -> None:
        mock_http_client.request.return_value = make_response(status_code=400)
        service = make_service()

        with pytest.raises(requests.HTTPError):
            getattr(service, method_name)(*args)


class TestAuthentication:
    """Internal certificate versus external token."""

    def test_internal_request_sends_the_client_cert(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.list_jobs()

        kwargs = mock_http_client.request.call_args.kwargs
        assert kwargs["cert"] == (
            "/home/tester/.toolskube/client.crt",
            "/home/tester/.toolskube/client.key",
        )
        assert kwargs["verify"] is False
        assert kwargs["timeout"] == REQUEST_TIMEOUT

    def test_internal_request_has_no_token_in_the_url(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.list_jobs()

        assert "token" not in mock_http_client.request.call_args.kwargs["url"]

    def test_external_request_appends_the_token(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service(token="secret")

        service.list_jobs()

        assert mock_http_client.request.call_args.kwargs["url"] == (
            f"{EXTERNAL_API_URL}/jobs/v1/tool/mytool/jobs?token=secret"
        )

    def test_external_request_sends_no_cert(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service(token="secret")

        service.list_jobs()

        kwargs = mock_http_client.request.call_args.kwargs
        assert "cert" not in kwargs
        assert kwargs["verify"] is True

    def test_token_and_include_unset_are_combined(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service(token="secret")

        service.list_jobs(include_unset=False)

        assert _query(mock_http_client.request.call_args.kwargs["url"]) == {
            "include_unset": ["false"],
            "token": ["secret"],
        }

    def test_write_requests_also_carry_the_token(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service(token="secret")

        service.create_job({"name": "x"})

        assert mock_http_client.request.call_args.kwargs["url"].endswith("/jobs?token=secret")

    def test_external_mode_without_token_raises(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service(internal=False)

        with pytest.raises(ValueError, match=TOKEN_ENV):
            service.list_jobs()

        mock_http_client.request.assert_not_called()


class TestErrors:
    """Error propagation."""

    def test_list_jobs_raises_on_server_error(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(status_code=500)
        service = make_service()

        with pytest.raises(requests.HTTPError):
            service.list_jobs()

    def test_connection_errors_are_not_swallowed(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        mock_http_client.request.side_effect = requests.ConnectionError("down")
        service = make_service()

        with pytest.raises(requests.ConnectionError):
            service.list_jobs()

    def test_missing_cert_oserror_is_not_swallowed(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        mock_http_client.request.side_effect = OSError("Could not find the TLS certificate file")
        service = make_service()

        with pytest.raises(OSError, match="TLS certificate"):
            service.list_jobs()


class TestInheritedEndpoints:
    """healthcheck() and metrics() come from the base class."""

    def test_healthcheck_path(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.healthcheck()

        assert mock_http_client.request.call_args.kwargs["url"] == f"{API_URL}/jobs/v1/healthz"

    def test_healthcheck_returns_payload(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(json_data={"status": "ok"})
        service = make_service()

        assert service.healthcheck() == {"status": "ok"}

    def test_metrics_path(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
    ) -> None:
        service = make_service()

        service.metrics()

        assert mock_http_client.request.call_args.kwargs["url"] == f"{API_URL}/jobs/v1/metrics"

    def test_metrics_returns_text(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(content=b"# HELP x", text="# HELP x")
        service = make_service()

        assert service.metrics() == "# HELP x"

    def test_redact_hides_the_token(
        self,
        make_service: Callable[..., ToolforgeJobsService],
    ) -> None:
        service = make_service(token="secret")

        assert service.redact("url?token=secret") == "url?token=***"


class TestRawRequest:
    """request() gives access to the raw response."""

    def test_returns_response_with_status_code(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        response = make_response(status_code=404)
        mock_http_client.request.return_value = response
        service = make_service()

        result = service.api.request("GET", "/jobs/v1/tool/mytool/jobs/missing", check=False)

        assert result is response
        assert result.status_code == 404


def test_restart_job_handles_api_error_response3(
    make_service: Callable[..., ToolforgeJobsService],
    mock_http_client,
    make_response,
) -> None:
    """Test that restart_job handles 400 API error response correctly."""
    # 1. Setup mock to simulate the 400 response body returned by the API
    error_payload = {"error": ["Unable to restart a one-off job"]}
    mock_response = make_response(status_code=400, json_data=error_payload)
    mock_http_client.request.return_value = mock_response

    service = make_service()

    # 2. Execute and assert that HTTPError is raised by default
    with pytest.raises(requests.HTTPError):
        service.restart_job("one-off-job")

    # 3. Assertions on the underlying request call
    mock_http_client.request.assert_called_once()
    assert mock_http_client.request.call_args.kwargs["method"] == "POST"
    assert mock_http_client.request.call_args.kwargs["url"].endswith("/jobs/one-off-job/restart")


def test_restart_job_returns_error_response_when_check_false(
    make_service: Callable[..., ToolforgeJobsService],
    mock_http_client,
    make_response,
) -> None:
    """Test that restart_job returns the error response when check=False (if supported)."""
    # 1. Setup mock response for error payload
    error_payload = {"error": ["Unable to restart a one-off job"]}
    mock_response = make_response(status_code=400, json_data=error_payload)
    mock_http_client.request.return_value = mock_response

    service = make_service()

    # 2. Execute request with check=False if the method supports it,
    # or test the raw request call directly:
    result = service.api.request("POST", "/jobs/one-off-job/restart", check=False)

    # 3. Assertions
    assert result.status_code == 400
    assert result.json() == error_payload


class TestStatusCodeDecidesTheShape:
    """The status code, not the shape of the body, tells success from error."""

    ERROR_BODY = {"error": ["Unable to restart a one-off job"], "warning": ["careful"]}

    @pytest.mark.parametrize("status_code", [400, 401, 404])
    def test_error_status_raises_with_the_bare_body_parsed(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
        status_code: int,
    ) -> None:
        mock_http_client.request.return_value = make_response(status_code=status_code, json_data=self.ERROR_BODY)
        service = make_service()

        with pytest.raises(ToolforgeApiError) as exc_info:
            service.restart_job("one-off-job")

        error = exc_info.value
        assert isinstance(error, requests.HTTPError)  # old `except HTTPError` code keeps working
        assert error.status_code == status_code
        assert error.response is not None
        assert isinstance(error.messages, ResponseMessages)
        assert error.messages.error == ["Unable to restart a one-off job"]
        assert error.messages.warning == ["careful"]
        assert "Unable to restart a one-off job" in str(error)

    @pytest.mark.parametrize(
        ("method_name", "args"),
        [
            ("images", ()),
            ("quotas", ()),
            ("list_jobs", ()),
            ("show_job", ("x",)),
            ("create_job", ({"name": "x"},)),
            ("update_job", ({"name": "x"},)),
            ("flush_jobs", ()),
            ("delete_job", ("x",)),
            ("restart_job", ("x",)),
            ("get_logs", ("x",)),
        ],
    )
    def test_every_endpoint_raises_on_error_status(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
        method_name: str,
        args: tuple,
    ) -> None:
        mock_http_client.request.return_value = make_response(status_code=404, json_data={"error": ["nope"]})
        service = make_service()

        with pytest.raises(ToolforgeApiError) as exc_info:
            getattr(service, method_name)(*args)

        assert exc_info.value.messages.error == ["nope"]

    def test_success_body_with_an_error_list_is_not_an_exception(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        """A 200 keeps the wrapped shape, even if it carries error messages."""
        mock_http_client.request.return_value = make_response(
            status_code=200, json_data={"messages": {"error": ["something odd"]}}
        )
        service = make_service()

        result = service.restart_job("x")

        assert isinstance(result, MessagesResponse)
        assert result.messages is not None
        assert result.messages.error == ["something odd"]

    def test_success_body_in_the_bare_shape_is_not_reinterpreted(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        """The shape is never guessed: a 200 body is always loaded as the success type."""
        mock_http_client.request.return_value = make_response(status_code=200, json_data={"error": ["x"]})
        service = make_service()

        assert service.restart_job("x").messages is None

    def test_error_status_with_non_json_body_still_raises(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(
            status_code=502, content=b"<html>", text="<html>", json_error=True
        )
        service = make_service()

        with pytest.raises(ToolforgeApiError) as exc_info:
            service.list_jobs()

        assert exc_info.value.status_code == 502
        assert exc_info.value.messages == ResponseMessages()

    def test_error_status_with_unexpected_body_shape_still_raises(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(status_code=400, json_data={"error": "not a list"})
        service = make_service()

        with pytest.raises(ToolforgeApiError) as exc_info:
            service.list_jobs()

        assert exc_info.value.messages == ResponseMessages()

    def test_error_status_with_json_list_body_still_raises(
        self,
        make_service: Callable[..., ToolforgeJobsService],
        mock_http_client,
        make_response,
    ) -> None:
        mock_http_client.request.return_value = make_response(status_code=500, json_data=["boom"])
        service = make_service()

        with pytest.raises(ToolforgeApiError) as exc_info:
            service.list_jobs()

        assert exc_info.value.messages == ResponseMessages()
