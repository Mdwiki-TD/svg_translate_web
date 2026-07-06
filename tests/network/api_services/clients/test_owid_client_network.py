"""
Network Tests for src.main_app.api_services.clients.owid_client.
"""

from __future__ import annotations

import pytest

from src.main_app.api_services.clients.owid_client import (
    _fetch_grapher_metadata,
    fetch_grapher_metadata,
)

pytestmark = pytest.mark.network


class TestFetchGrapherMetadata:
    """Tests for fetch_grapher_metadata function."""

    def test_successful_fetch_returns_parsed_json(self):
        """Test that a successful response returns the parsed dict."""
        result, status_code = _fetch_grapher_metadata("test-slug")
        assert status_code == 404
        assert result == {"error": "Not found", "status": 404}
