"""
Tests for src/main_app/api_services/pages_api.py
"""

from __future__ import annotations

import pytest

from src.main_app.api_services.pages_api import (
    create_page,
    move_page,
    update_page_text,
)
from tests.network.network_conftest import TestNetwork

pytestmark = pytest.mark.network


class TestCreatePageNetwork(TestNetwork):
    """Real Tests for the create_page function."""


class TestUpdatePageTextNetwork(TestNetwork):
    """Real Tests for update_page_text function."""
