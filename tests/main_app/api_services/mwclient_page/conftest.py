
from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from src.main_app.api_services.mwclient_page import MwClientPage


# ── fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_site() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_exists_page() -> MagicMock:
    page = MagicMock()
    page.exists = True
    return page


@pytest.fixture
def mw_client(mock_site: MagicMock) -> MwClientPage:
    return MwClientPage("Test Page", mock_site)
