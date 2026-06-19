"""
Comprehensive unit tests for download_step module.
Tests cover download functionality, and error handling.
"""

from unittest.mock import MagicMock

import pytest


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


@pytest.fixture
def mock_download_core(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.api_services.files_service.download_file_utils.download_file_rate_limit",
        _mock,
    )
    return _mock
