"""Focused unit tests for routes_utils helpers (pure functions)."""

from datetime import datetime

from src.main_app.app_routes.utils.routes_utils import (
    load_auth_payload,
)



def test_load_auth_payload_happy_path():
    class U:
        user_id = 9
        username = "user9"
        access_token = "ak"  # noqa: S105
        access_secret = "as"  # noqa: S105

    payload = load_auth_payload(U())
    assert payload["id"] == 9
    assert payload["username"] == "user9"
    assert payload["access_token"] == "ak"  # noqa: S105
    assert payload["access_secret"] == "as"  # noqa: S105
