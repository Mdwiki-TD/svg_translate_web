"""Tests for the fix_nested routes blueprint."""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask

from src.app import create_app
from src.app.app_routes.fix_nested import routes


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch) -> tuple[Flask, Any]:
    """Provide a Flask test client for fix_nested routes."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key")
    app = create_app()
    app.config["TESTING"] = True
    yield app, app.test_client()


def test_fix_nested_post_requires_oauth_no_localhost(
    app_client: tuple[Flask, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that POST redirects to OAuth login when not authenticated."""
    app, client = app_client

    # Mock current_user to return None (not logged in)
    monkeypatch.setattr(routes, "current_user", lambda: None)

    response = client.post("/fix_nested/", data={"filename": "test.svg"})
    assert response.status_code == 302
    assert "login" in response.headers["Location"]


def test_fix_nested_post_preserves_filename_before_oauth_no_localhost(
    app_client: tuple[Flask, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that filename is saved to session before OAuth redirect."""
    app, client = app_client

    monkeypatch.setattr(routes, "current_user", lambda: None)

    response = client.post("/fix_nested/", data={"filename": "preserved_file.svg"})
    assert response.status_code == 302

    # Check that the filename was saved in session for restoration after OAuth
    with client.session_transaction() as sess:
        assert sess.get(routes.FIX_NESTED_FILENAME_KEY) == "preserved_file.svg"


@pytest.mark.skip(reason="OAuth not required on localhost")
def test_fix_nested_post_requires_oauth(
    app_client: tuple[Flask, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that POST redirects to OAuth login when not authenticated."""
    app, client = app_client

    # Mock current_user to return None (not logged in)
    monkeypatch.setattr(routes, "current_user", lambda: None)

    response = client.post("/fix_nested/", data={"filename": "test.svg"})
    assert response.status_code != 302
    assert "login" in response.headers["Location"]


@pytest.mark.skip(reason="OAuth not required on localhost")
def test_fix_nested_post_preserves_filename_before_oauth(
    app_client: tuple[Flask, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that filename is saved to session before OAuth redirect."""
    app, client = app_client

    monkeypatch.setattr(routes, "current_user", lambda: None)

    response = client.post("/fix_nested/", data={"filename": "preserved_file.svg"})
    assert response.status_code != 302

    # Check that the filename was saved in session for restoration after OAuth
    with client.session_transaction() as sess:
        assert sess.get(routes.FIX_NESTED_FILENAME_KEY) == "preserved_file.svg"
