"""
Network tests for src/main_app/api_services/query_api.py module.

Functions to test: get_template_pages, is_pages_exists, resolve_redirects, search_pages, get_page_links

TODO: write tests
"""

import pytest

from src.main_app.api_services.query_api import (
    get_page_links,
    get_template_pages,
    is_pages_exists,
    resolve_redirects,
    search_pages,
)
from tests.network.network_conftest import TestNetwork

pytestmark = pytest.mark.network


class TestGetPageLinksNetwork(TestNetwork):
    """Real Tests for the get_page_links function."""


class TestGetTemplatePagesNetwork(TestNetwork):
    """Real Tests for the get_template_pages function."""


class TestIsPagesExistsNetwork(TestNetwork):
    """Real Tests for the is_pages_exists function."""

    def test_basic(self) -> None:
        result = is_pages_exists(["OWID/Academic freedom index"], self.site)
        assert result == {"OWID/Academic freedom index": True}


class TestResolveRedirectsNetwork(TestNetwork):
    """Real Tests for the resolve_redirects function."""


class TestSearchPagesNetwork(TestNetwork):
    """Real Tests for the search_pages function."""
