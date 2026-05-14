"""Configuration and fixtures for pytest"""

import os
import secrets
import sys
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from cryptography.fernet import Fernet
from flask.app import Flask
from flask.testing import FlaskClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

# ── Set ALL env vars before any src.* import ─────────────────────────────────
# config.py executes get_settings() at module level and raises RuntimeError
# if FLASK_SECRET_KEY is missing, so every env var must be set here first,
# before any import that pulls in src.main_app.
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("OAUTH_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
os.environ.setdefault("OAUTH_CONSUMER_KEY", "test-consumer-key")
os.environ.setdefault("OAUTH_CONSUMER_SECRET", "test-consumer-secret")
os.environ.setdefault("OAUTH_MWURI", "https://example.org/w/index.php")

# ── Now safe to import third-party and src packages ──────────────────────────


_CopySVGTranslation_PATH = os.getenv(
    "CopySVGTranslation_PATH", "I:/TOOLFORGE_TOOLS/SVG_PY/CopySVGTranslation/CopySVGTranslation"
)
if _CopySVGTranslation_PATH and Path(_CopySVGTranslation_PATH).is_dir():
    sys.path.insert(0, str(Path(_CopySVGTranslation_PATH).parent))

# Import after environment setup
from src.main_app import create_app
from src.main_app.api_services.mwclient_page import MwClientPage  # noqa: E402
from src.main_app.config import TestingConfig


@pytest.fixture(autouse=True)
def disable_network(mocker):
    """Disable all network requests during testing"""
    mocker.patch("requests.get", side_effect=Exception("Network disabled in tests"))
    mocker.patch("requests.post", side_effect=Exception("Network disabled in tests"))
    mocker.patch("urllib.request.urlopen", side_effect=Exception("Network disabled in tests"))


@pytest.fixture
def app() -> Generator[Flask, Any, None]:
    """Create and configure a test Flask application.

    Yields:
        Flask application configured for testing.
    """
    app = create_app(TestingConfig)

    with app.app_context():
        yield app


@pytest.fixture
def app_mock():
    app = Flask(__name__)
    app.secret_key = "test"
    return app


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a test client for the app.

    Args:
        app: The Flask application fixture.

    Returns:
        Test client for making HTTP requests.
    """
    return app.test_client()


@pytest.fixture
def csrf_token():
    """Helper fixture to generate CSRF tokens for tests."""

    def _get_csrf_token(client: Any) -> str:
        """Get a CSRF token by making a GET request and extracting it."""
        import re

        response = client.get("/")
        match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
        if match:
            return match.group(1).decode()
        # If not found in response, try to generate one from the test request context
        from flask_wtf.csrf import generate_csrf

        with client.application.test_request_context():
            return generate_csrf()

    return _get_csrf_token


@pytest.fixture
def sample_from_prompt() -> str:
    """Sample wikitext similar to the user's prompt."""
    return (
        "*[[Commons:List of interactive graphs|Return to list]]\n"
        "{{owidslider\n"
        "|start        = 2022\n"
        "|list         = Template:OWID/health expenditure government expenditure#gallery\n"
        "|location     = commons\n"
        "|caption      = \n"
        "|title        = \n"
        "|language     = \n"
        "|file         = [[File:Health-expenditure-government-expenditure,World,2022 (cropped).svg|link=|thumb|upright=1.6|Health expenditure government expenditure]]\n"
        "|startingView = World\n"
        "}}\n"
        '<syntaxhighlight lang="wikitext" style="overflow:auto;">\n'
        "{{owidslider\n"
        "|start        = 2022\n"
        "|list         = Template:OWID/health expenditure government expenditure#gallery\n"
        "|location     = commons\n"
        "|caption      = \n"
        "|title        = \n"
        "|language     = \n"
        "|file         = [[File:Health-expenditure-government-expenditure,World,2022 (cropped).svg|link=|thumb|upright=1.6|Health expenditure government expenditure]]\n"
        "|startingView = World\n"
        "}}\n"
        "</syntaxhighlight>\n"
        "*'''Source''': https://ourworldindata.org/grapher/health-expenditure-government-expenditure\n"
        "*'''Translate''':  https://svgtranslate.toolforge.org/File:health-expenditure-government-expenditure,World,2000.svg\n"
        "\n"
        "==Data==\n"
        "{{owidslidersrcs|id=gallery|widths=240|heights=240\n"
        "|gallery-AllCountries=\n"
        "File:health-expenditure-government-expenditure, 2000 to 2021, UKR.svg!country=UKR\n"
        "File:health-expenditure-government-expenditure, 2002 to 2022, AFG.svg!country=AFG\n"
        "File:health-expenditure-government-expenditure, 2000 to 2022, BGD.svg!country=BGD\n"
        "File:health-expenditure-government-expenditure, 2000 to 2022, FSM.svg!country=FSM\n"
        "File:health-expenditure-government-expenditure, 2000 to 2022, ERI.svg!country=ERI\n"
        "File:health-expenditure-government-expenditure, 2017 to 2022, SSD.svg!country=SSD\n"
        "File:health-expenditure-government-expenditure, 2013 to 2022, SOM.svg!country=SOM\n"
        "File:health-expenditure-government-expenditure, 2000 to 2022, YEM.svg!country=YEM\n"
        "}}\n"
    )


@pytest.fixture
def sample_with_both_titles() -> str:
    """Wikitext with both SVGLanguages and Translate line. SVGLanguages should take precedence."""
    return (
        "{{SVGLanguages|some_main_title,World,2010.svg}}\n"
        "*'''Translate''': https://svgtranslate.toolforge.org/File:another-title,World,2005.svg\n"
    )


@pytest.fixture
def mock_jobs_service(monkeypatch: pytest.MonkeyPatch):
    """Mock the jobs_service.is_job_cancelled function to avoid database calls.

    This fixture mocks the is_job_cancelled function to return False by default,
    allowing worker tests to run without requiring database configuration.

    Returns:
        MagicMock: The mock is_job_cancelled function that can be configured per test.
    """

    mock_is_cancelled = MagicMock(return_value=False)
    monkeypatch.setattr(
        "src.main_app.db.services.jobs_service.is_job_cancelled",
        mock_is_cancelled,
    )

    return mock_is_cancelled


@pytest.fixture
def sample_without_titles() -> str:
    """Wikitext lacking both SVGLanguages and Translate line."""
    return "No main title here.\n{{owidslidersrcs|id=x|widths=100|heights=100|gallery-AllCountries=}}\n"


@pytest.fixture
def sample_with_svglanguages_only() -> str:
    """Wikitext with only SVGLanguages main title."""
    return "{{SVGLanguages|parkinsons-disease-prevalence-ihme,World,1990.svg}}\nSome other text...\n"


@pytest.fixture
def sample_multiple_owidslidersrcs() -> str:
    """Wikitext containing multiple owidslidersrcs blocks and duplicate filenames."""
    return (
        "{{owidslidersrcs|id=a|widths=120|heights=120|gallery-AllCountries=\n"
        "File:Alpha, 2000 to 2001, AAA.svg!country=AAA\n"
        "File:Beta, 2001 to 2002, BBB.svg!country=BBB\n"
        "}}\n"
        "{{owidslidersrcs|id=b|widths=120|heights=120|gallery-AllCountries=\n"
        "File:Beta, 2001 to 2002, BBB.svg!country=BBB\n"  # duplicate on purpose
        "File:Gamma, 2002 to 2003, CCC.svg!country=CCC\n"
        "}}\n"
    )


# ── mwclient_page fixtures ───────────────────────────────────────────────────────────────────


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


@pytest.fixture(autouse=True)
def setup_db():
    """Initialize an in-memory SQLite database for tests.

    Creates a fresh SQLite in-memory engine for every test and patches
    engine_mod._SessionFactory so all sqlalchemy_db service calls use it.
    View-backed tables (is_view=True) are skipped since SQLite cannot run
    the MySQL CREATE VIEW statements.
    """
    from src.main_app.sqlalchemy_db import engine as engine_mod
    from src.main_app.sqlalchemy_db.engine import (
        BaseDb,
        build_engine,
    )

    engine = build_engine("sqlite:///:memory:")

    # Create only real tables; skip view-backed mapped classes
    for table in BaseDb.metadata.sorted_tables:
        if not table.info.get("is_view"):
            table.create(engine, checkfirst=True)

    # Create views manually
    for table in BaseDb.metadata.sorted_tables:
        if table.info.get("is_view") and table.info.get("create_query"):
            with engine.connect() as conn:
                conn.execute(text(table.info["create_query"]))

    factory = sessionmaker(bind=engine, expire_on_commit=False)

    with patch.object(engine_mod, "_SessionFactory", factory):
        yield

    engine.dispose()
