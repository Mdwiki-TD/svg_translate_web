"""Shared pytest fixtures.

Boot a Flask app once per session with CSRF on (so tests exercise the
real protection path) and provide helpers for scraping CSRF tokens and
for switching session identity. Each test gets a fresh JobStore so jobs
don't leak across tests.
"""

from __future__ import annotations

import logging
import os
import secrets
import sys
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from cryptography.fernet import Fernet
from flask.app import Flask
from flask.testing import FlaskClient
from pytest_socket import disable_socket
from sqlalchemy import text

# Make the src/ directory importable as `main_app`. The repo's prod
# entrypoint src/app.py does the same trick.
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

# ── Set ALL env vars before any src.* import ─────────────────────────────────
# config.py executes get_settings() at module level and raises RuntimeError
# if FLASK_SECRET_KEY is missing, so every env var must be set here first,
# before any import that pulls in src.main_app.
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("FLASK_ENV", "testing")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("OAUTH_ENCRYPTION_KEY", Fernet.generate_key().decode("utf-8"))
os.environ.setdefault("OAUTH_CONSUMER_KEY", "test-consumer-key")
os.environ.setdefault("OAUTH_CONSUMER_SECRET", "test-consumer-secret")
os.environ.setdefault("OAUTH_MWURI", "https://example.org/w/index.php")
os.environ.setdefault("WIKI_DOMAIN", "test.wikipedia.org")

# ── Now safe to import third-party and src packages ──────────────────────────

_CopySVGTranslation_PATH = os.getenv(
    "CopySVGTranslation_PATH", "I:/TOOLFORGE_TOOLS/SVG_PY/CopySVGTranslation/CopySVGTranslation"
)
if _CopySVGTranslation_PATH and Path(_CopySVGTranslation_PATH).is_dir():
    sys.path.insert(0, str(Path(_CopySVGTranslation_PATH).parent))

# Import after environment setup
from src.main_app import create_app  # noqa: E402
from src.main_app.config import TestingConfig  # noqa: E402
from src.main_app.extensions import db as _db  # noqa: E402


@pytest.fixture(autouse=True)
def stop_nets(request):
    # Check if 'network' mark is present in the current test item
    if "network" in request.node.keywords:
        from pytest_socket import enable_socket

        enable_socket()
        return
    # Otherwise, disable the socket for all other tests
    disable_socket(allow_unix_socket=True)


# ── app fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def mock_app() -> Generator[Flask, Any, None]:  # noqa: UP043
    """
    Create and configure a test Flask application.
    """
    application = create_app(TestingConfig)
    application.config.update(TESTING=True)

    with application.app_context():
        yield application


@pytest.fixture
def mock_client(mock_app: Flask) -> FlaskClient:
    """Fresh test client per test."""

    return mock_app.test_client()


@pytest.fixture
def mock_login(mock_client):
    """Helper to set ``session['username']`` to a given user."""

    def _login(username: str) -> None:
        with mock_client.session_transaction() as session:
            session["username"] = username

    return _login


# ── db fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def setup_db(mock_app):
    """Initialize an in-memory SQLite database for tests using Flask-SQLAlchemy.

    Creates all real tables (skipping views) and creates views manually.
    The Flask-SQLAlchemy session (db.session) is used throughout tests.
    """
    with mock_app.app_context():
        # Create only real tables; skip view-backed mapped classes
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.create_all(_db.engine, tables=real_tables, checkfirst=True)

        from sqlalchemy import inspect as sa_inspect

        existing_views = set(sa_inspect(_db.engine).get_view_names())
        # Create views manually (SQLite-compatible CREATE VIEW)
        with _db.engine.connect() as conn:
            for table in _db.metadata.tables.values():
                if not table.info.get("is_view"):
                    continue

                if not table.info.get("create_query"):
                    logging.warning("View %s has no create_query, skipping", table.name)
                    continue

                if table.name in existing_views:
                    continue
                try:
                    create_sql = table.info["create_query"]
                    conn.execute(text(create_sql))
                    conn.commit()
                except Exception:
                    conn.rollback()
                    logging.exception("Failed to create view %s", table.name)

        yield

        _db.session.remove()

        # Drop views first (SQLite requires DROP VIEW, not DROP TABLE)
        with _db.engine.connect() as conn:
            for table in _db.metadata.tables.values():
                if table.info.get("is_view"):
                    try:
                        conn.execute(text(f"DROP VIEW IF EXISTS {table.name}"))
                    except Exception:
                        pass
            conn.commit()

        # Drop only real tables
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.drop_all(_db.engine, tables=real_tables)


# ── mwclient_page fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_site() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_page() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_site_pages(mock_site, mock_page):
    def _factory(page_exists: bool) -> MagicMock:
        mock_page.exists = page_exists

        mock_pages = MagicMock()
        mock_pages.__getitem__ = MagicMock(return_value=mock_page)

        mock_site.pages = mock_pages
        return mock_site

    return _factory
