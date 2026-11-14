from unittest.mock import MagicMock

import pytest
import requests
from src.main_app.admin.routes_services.toolforge_jobs_service import JobsPageService
from src.main_app.api_services.clients.toolforge.toolforge_jobs_api_service import (
    ToolforgeApiError,
    ToolforgeJobsService,
)


def test_json_raises_with_the_parsed_body_on_a_400():
    """The status code decides: a 400 raises ToolforgeApiError carrying the bare error body."""
    # 1. Initialize the service with dummy parameters to avoid real network calls
    service = ToolforgeJobsService(tool_name="test-tool")

    # 2. Mock the internal api client response
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 400
    # Simulate the JSON error body returned by the API

    error_payload = {"error": ["Unable to restart a one-off job"]}  # The real response from API

    mock_response.json.return_value = error_payload

    # Attach the mock to service.api.request
    service.api.request = MagicMock(return_value=mock_response)

    # 3. Call the method under test
    with pytest.raises(ToolforgeApiError) as exc_info:
        service._json("POST", "/jobs/some-job/restart")

    assert exc_info.value.messages.error == error_payload["error"]

    with pytest.raises(ToolforgeApiError) as exc_info2:
        service.restart_job("some-job")
    assert exc_info2.value.status_code == 400
    assert exc_info2.value.messages.error == error_payload["error"]


def test_restart_job_success():
    """Test that restart_job successfully restarts a job and returns an OK result

    with a success message.
    """
    # 1. Mock the ToolforgeJobsService client
    mock_toolforge = MagicMock()
    mock_toolforge.restart_job.return_value = {"messages": []}

    # 2. Initialize JobsPageService with the mocked service
    page_service = JobsPageService(toolforge=mock_toolforge)

    # 3. Call restart_job
    result = page_service.restart_job("some-job")

    # 4. Assertions
    assert result.ok is True
    assert ("Job 'some-job' restarted.", "success") in result.messages
    mock_toolforge.restart_job.assert_called_once_with("some-job")


def test_restart_job_success1():
    """Test successful job restart returns success message and ok=True."""
    # 1. Setup mock service to return a normal payload
    mock_toolforge = MagicMock()
    mock_toolforge.restart_job.return_value = {"messages": {"info": ["Job queued successfully"]}}

    page_service = JobsPageService(toolforge=mock_toolforge)

    # 2. Execute
    result = page_service.restart_job("my-cron-job")

    # 3. Assertions
    assert result.ok is True
    assert ("Job 'my-cron-job' restarted.", "success") in result.messages
    assert ("Job queued successfully", "info") in result.messages
    mock_toolforge.restart_job.assert_called_once_with("my-cron-job")


def test_restart_job_invalid_name():
    """Test that restart_job returns an error result when an invalid job name

    is provided without calling the API.
    """
    mock_toolforge = MagicMock()
    page_service = JobsPageService(toolforge=mock_toolforge)

    # Use an invalid job name (e.g., contains spaces or invalid characters)
    result = page_service.restart_job("invalid job name!")

    # Assertions
    assert result.ok is False
    assert any("Invalid job name" in msg[0] for msg in result.messages)
    mock_toolforge.restart_job.assert_not_called()


def test_restart_job_handles_http_400_error():
    """Test that restart_job gracefully handles an HTTP 400 error (e.g., trying

    to restart a one-off job) and returns an error result.
    """
    # 1. Setup mock to raise requests.HTTPError with a 400 status code
    mock_toolforge = MagicMock()

    response = MagicMock(spec=requests.Response)
    response.status_code = 400
    http_error = requests.HTTPError(response=response)

    mock_toolforge.restart_job.side_effect = http_error

    page_service = JobsPageService(toolforge=mock_toolforge)

    # 2. Call restart_job
    result = page_service.restart_job("some-job")

    # 3. Assertions
    assert result.ok is False
    assert (
        "Failed to restart job 'some-job': bad request (400).",
        "danger",
    ) in result.messages
    mock_toolforge.restart_job.assert_called_once_with("some-job")


def test_restart_job_handles_api_error_response():
    """Test that 400 API response with {'error': [...]} sets ok=False

    and correctly passes the error message 'Unable to restart a one-off job'.
    """
    # 1. Setup mock to simulate the 400 response body returned by ToolforgeJobsService._json
    # mock_toolforge = MagicMock()
    # mock_toolforge.restart_job.return_value = {"error": ["Unable to restart a one-off job"]}

    # 2. Mock the internal api client response
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 400
    # Simulate the JSON error body returned by the API
    error_payload = {"error": ["Unable to restart a one-off job"]}  # The real response from API
    mock_response.json.return_value = error_payload

    service = ToolforgeJobsService(tool_name="test-tool")
    page_service = JobsPageService(toolforge=service)

    # Attach the mock to service.api.request
    service.api.request = MagicMock(return_value=mock_response)

    # 2. Execute
    result = page_service.restart_job("one-off-job")

    # 3. Assertions
    assert ("Unable to restart a one-off job", "danger") in result.messages
    assert ("Job 'one-off-job' restarted.", "success") not in result.messages
    # mock_toolforge.restart_job.assert_called_once_with("one-off-job")

    assert result.ok is False


def test_restart_job_invalid_job_name():
    """Test that restart_job rejects invalid job names without calling the API."""
    mock_toolforge = MagicMock()
    page_service = JobsPageService(toolforge=mock_toolforge)

    # Invalid job name (contains capital letters and spaces)
    result = page_service.restart_job("Invalid Job Name!")

    assert result.ok is False
    assert any(msg[1] == "danger" and "Invalid job name" in msg[0] for msg in result.messages)
    mock_toolforge.restart_job.assert_not_called()


def test_restart_job_handles_http_exception():
    """Test that HTTP exceptions (e.g. 500 or 401 without JSON body) are caught cleanly."""
    mock_toolforge = MagicMock()

    # Simulate an raised HTTPError exception
    response = MagicMock(spec=requests.Response)
    response.status_code = 401
    mock_toolforge.restart_job.side_effect = requests.HTTPError(response=response)

    page_service = JobsPageService(toolforge=mock_toolforge)

    result = page_service.restart_job("my-cron-job")

    assert result.ok is False
    assert any("unauthorized (401)" in msg[0] for msg in result.messages)


def test_restart_job_api_error_flows_through_the_typed_exception():
    """End to end: a 404 with a bare body becomes flash messages, never a success."""
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 404
    mock_response.json.return_value = {"error": ["Job 'x' does not exist"]}

    service = ToolforgeJobsService(tool_name="test-tool")
    service.api.request = MagicMock(return_value=mock_response)
    page_service = JobsPageService(toolforge=service)

    result = page_service.restart_job("x")

    assert result.ok is False
    assert ("Job 'x' does not exist", "danger") in result.messages
    assert any("not found (404)" in text for text, _ in result.messages)


def test_server_error_does_not_flash_an_empty_message():
    """A status code without specific text (500) must not add a ("", "") message."""
    response = MagicMock(spec=requests.Response)
    response.status_code = 500
    response.json.return_value = {}
    mock_toolforge = MagicMock()
    mock_toolforge.api.redact.side_effect = lambda text: text
    mock_toolforge.restart_job.side_effect = requests.HTTPError("boom", response=response)

    result = JobsPageService(toolforge=mock_toolforge).restart_job("some-job")

    assert result.ok is False
    assert ("", "") not in result.messages
    assert result.messages[0][1] == "danger"
    assert "Failed to restart job 'some-job'" in result.messages[0][0]


def test_unexpected_api_shape_is_a_flash_message_not_a_crash():
    """DaciteError (shape the types do not expect) is handled like any API failure."""
    from dacite import DaciteError

    mock_toolforge = MagicMock()
    mock_toolforge.api.redact.side_effect = lambda text: text
    mock_toolforge.list_jobs.side_effect = DaciteError("wrong type for job_type")

    page = JobsPageService(toolforge=mock_toolforge).build_jobs_page()

    assert page.error is True
    assert page.messages and page.messages[0][1] == "danger"


def test_extract_messages_accepts_dataclasses_and_dicts():
    from src.main_app.api_services.clients.toolforge.toolforge_jobs_types import (
        MessagesResponse,
        ResponseMessages,
    )

    extract = JobsPageService._extract_messages
    assert extract(MessagesResponse(messages=ResponseMessages(info=["a"], error=[]))) == {"info": ["a"]}
    assert extract(ResponseMessages(error=["boom"])) == {"error": ["boom"]}
    assert extract(MessagesResponse()) == {}
    assert extract({"messages": {"warning": ["w"]}}) == {"warning": ["w"]}
    assert extract({"error": ["bare"]}) == {"error": ["bare"]}
    assert extract({"messages": []}) == {}
    assert extract("not a payload") == {}
