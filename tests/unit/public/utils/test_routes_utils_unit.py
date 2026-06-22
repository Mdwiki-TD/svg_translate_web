"""Focused unit tests for routes_utils helpers (pure functions)."""

from src.main_app.public.utils.routes_utils import (
    load_auth_payload,
)


def test_load_auth_payload_happy_path():
    class U:
        user_id = 9
        username = "user9"
        access_token = "ak"
        access_secret = "as"

    payload = load_auth_payload(U())
    assert payload["id"] == 9
    assert payload["username"] == "user9"
    assert payload["access_token"] == "ak"
    assert payload["access_secret"] == "as"
