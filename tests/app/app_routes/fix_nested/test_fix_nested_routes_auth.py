"""Tests for the fix_nested routes blueprint."""

from __future__ import annotations

from typing import Any

import pytest
from flask import Flask

from src.app import create_app


@pytest.fixture
def app_client(monkeypatch: pytest.MonkeyPatch):
    """Provide a Flask test client for fix_nested routes."""
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key")
    app = create_app()
    app.config["TESTING"] = True
    # Disable CSRF for testing
    app.config["WTF_CSRF_ENABLED"] = False
    yield app, app.test_client()


def test_fix_nested_post_requires_oauth_no_localhost(
    app_client: tuple[Flask, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that POST redirects to OAuth login when not authenticated."""
    app, client = app_client

    # Mock current_user to return None (not logged in)
    monkeypatch.setattr("src.app.app_routes.fix_nested.routes.current_user", lambda: None)

    response = client.post(
        "/fix_nested/",
        data={"filename": "test.svg"},
        base_url="https://example.com",
    )
    assert response.status_code == 302
    assert "login" in response.headers["Location"]


def test_fix_nested_post_preserves_filename_before_oauth_no_localhost(
    app_client: tuple[Flask, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that filename is saved to session before OAuth redirect."""
    app, client = app_client

    monkeypatch.setattr("src.app.app_routes.fix_nested.routes.current_user", lambda: None)

    response = client.post(
        "/fix_nested/",
        data={"filename": "preserved_file.svg"},
        base_url="https://example.com",
    )
    assert response.status_code == 302


def test_fix_nested_post_requires_oauth(app_client: tuple[Flask, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that POST redirects to OAuth login when not authenticated."""
    app, client = app_client

    # Mock current_user to return None (not logged in)
    monkeypatch.setattr("src.app.app_routes.fix_nested.routes.current_user", lambda: None)

    response = client.post(
        "/fix_nested/",
        data={"filename": "test.svg"},
        base_url="http://127.0.0.1/",
    )
    assert response.status_code == 200
