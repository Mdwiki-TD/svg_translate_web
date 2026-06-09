"""
Tests for src/main_app/api_services/pages_api.py
"""

from __future__ import annotations

import pytest

from src.main_app.api_services.mwclient_page import (
    MwClientPage,
)
from tests.network.network_conftest import TestNetwork

pytestmark = pytest.mark.network


class TestMwClientPageNetwork(TestNetwork):
    """Real Tests for the is_page_exists function."""


class TestCreatePageNetwork(TestNetwork):
    """Real Tests for the create_page function."""


class TestUpdatePageTextNetwork(TestNetwork):
    """Real Tests for update_page_text function."""
