"""
Network Tests for src.main_app.api_services.clients.owid_client.
"""

from __future__ import annotations

import pytest

from src.main_app.api_services.clients.owid_client import (
    fetch_grapher_metadata,
)

pytestmark = pytest.mark.network

class TestFetchGrapherMetadata:
    """Tests for fetch_grapher_metadata function."""

    def test_successful_fetch_returns_parsed_json(self):
        """Test that a successful response returns the parsed dict."""
        result = fetch_grapher_metadata("test-slug")

        assert result == {"name": "chart", "data": [1, 2, 3]}
