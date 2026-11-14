from unittest.mock import MagicMock

import requests
from src.main_app.admin.routes_services.toolforge_jobs_service import JobsPageService
from src.main_app.api_services.clients.toolforge.toolforge_jobs_api_service import (
    ToolforgeJobsService,
)


def test_json_handles_400_error_with_json_body():
    """Test that _json correctly parses and returns the JSON error body

    when receiving a 400 Bad Request status code.
    """
    # 1. Initialize the service with dummy parameters to avoid real network calls
    service = ToolforgeJobsService(tool_name="test-tool")

    # 2. Mock the internal api client response
    mock_response = MagicMock(spec=requests.Response)
    mock_response.status_code = 400
    # Simulate the JSON error body returned by the API
    error_payload = {"error": ["Unable to restart a one-off job"]}
    mock_response.json.return_value = error_payload

    # Attach the mock to service.api.request
    service.api.request = MagicMock(return_value=mock_response)

    # 3. Call the method under test
    result = service._json("POST", "/jobs/some-job/restart")

    # 4. Assert that the error dictionary was successfully returned despite the 400 status
    assert result == error_payload
    # service.api.request.assert_called_once_with("POST", "/jobs/some-job/restart", params=None, json=None, check=True)

    result2 = service.restart_job("some-job")
    # assert result2.to_json() == error_payload
    assert result2 == error_payload


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
    assert ("Failed to restart job 'some-job': bad request (400).", "danger") in result.messages
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
    error_payload = {"error": ["Unable to restart a one-off job"]}
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
