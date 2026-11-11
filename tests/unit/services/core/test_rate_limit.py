"""Unit tests for src.main_app.services.core.rate_limit (Flask-Limiter based)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from src.main_app.services.core.rate_limit import (
    CALLBACK_LIMIT_STRATEGY,
    LOGIN_LIMIT_STRATEGY,
    callback_limit,
    init_rate_limiter,
    limiter,
    login_limit,
)

CLIENT_A = "10.0.0.1"
CLIENT_B = "10.0.0.2"


def _count(limit: str) -> int:
    """Extract the numeric part of a limit string such as '5 per minute'."""
    return int(limit.split()[0])


def _get(client: FlaskClient, path: str, ip: str = CLIENT_A, **headers: str):
    return client.get(path, environ_overrides={"REMOTE_ADDR": ip}, headers=headers)


@pytest.fixture(scope="module")
def client() -> Iterator[FlaskClient]:
    """Minimal app with one route per limit.

    Built once per module: decorator limits are registered by function name,
    so re-creating the routes for every test could stack duplicate limits.
    """
    app = Flask(__name__)
    app.config.update(
        RATELIMIT_STORAGE_URI="memory://",
        RATELIMIT_HEADERS_ENABLED=True,
    )
    init_rate_limiter(app)

    @app.get("/login")
    @login_limit
    def login() -> str:
        return "ok"

    @app.get("/callback")
    @callback_limit
    def callback() -> str:
        return "ok"

    @app.errorhandler(429)
    def too_many(e):
        return {"error": "Too many requests"}, 429

    yield app.test_client()


@pytest.fixture(autouse=True)
def _reset_counters(client: FlaskClient) -> Iterator[None]:
    limiter.reset()
    yield
    limiter.reset()


def test_limit_values() -> None:
    assert LOGIN_LIMIT_STRATEGY == "5 per minute"
    assert CALLBACK_LIMIT_STRATEGY == "10 per minute"


@pytest.mark.parametrize(
    ("path", "limit"),
    [("/login", LOGIN_LIMIT_STRATEGY), ("/callback", CALLBACK_LIMIT_STRATEGY)],
)
def test_allows_up_to_limit_then_returns_429(client: FlaskClient, path: str, limit: str) -> None:
    for _ in range(_count(limit)):
        assert _get(client, path).status_code == 200

    response = _get(client, path)

    assert response.status_code == 429
    assert response.get_json()["error"] == "Too many requests"
    assert "Retry-After" in response.headers


def test_limits_are_per_endpoint(client: FlaskClient) -> None:
    for _ in range(_count(LOGIN_LIMIT_STRATEGY)):
        _get(client, "/login")
    assert _get(client, "/login").status_code == 429

    assert _get(client, "/callback").status_code == 200


def test_limits_are_per_client(client: FlaskClient) -> None:
    for _ in range(_count(LOGIN_LIMIT_STRATEGY)):
        _get(client, "/login", ip=CLIENT_A)
    assert _get(client, "/login", ip=CLIENT_A).status_code == 429

    assert _get(client, "/login", ip=CLIENT_B).status_code == 200


def test_spoofed_forwarded_for_does_not_bypass_limit(client: FlaskClient) -> None:
    for i in range(_count(LOGIN_LIMIT_STRATEGY)):
        _get(client, "/login", **{"X-Forwarded-For": f"1.1.1.{i}"})

    response = _get(client, "/login", **{"X-Forwarded-For": "9.9.9.9"})

    assert response.status_code == 429
