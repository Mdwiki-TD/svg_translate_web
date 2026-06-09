"""
Tests for src/main_app/api_services/mwclient_page.py
"""

from __future__ import annotations

import pytest

from src.main_app.api_services.mwclient_page import (
    _handle_api_error,
    MwClientPage,
)
from tests.network.network_conftest import TestNetwork

pytestmark = pytest.mark.network


class TestMwClientPage(TestNetwork):
    """Real Tests for MwClientPage class."""

class TestLoadPage(TestNetwork):
    """Real Tests for load_page function."""

class TestCreate(TestNetwork):
    """Real Tests for create/create_page function."""

class TestEdit(TestNetwork):
    """Real Tests for edit/edit_page function."""

class TestExists(TestNetwork):
    """Real Tests for exists/check_exists function."""

class TestGetRedirectTarget(TestNetwork):
    """Real Tests for get_redirect_target function."""

class TestIsRedirect(TestNetwork):
    """Real Tests for is_redirect function."""

class TestMove(TestNetwork):
    """Real Tests for move/move_page function."""
