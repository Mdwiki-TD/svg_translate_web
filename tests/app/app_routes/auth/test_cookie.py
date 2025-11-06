"""
Tests for cookie signing and verification.
"""
import time
from unittest.mock import patch

from src.app.app_routes.auth.cookie import (
    extract_user_id,
    sign_state_token,
    sign_user_id,
    verify_state_token,
)


class MockCookieConfig:
    def __init__(self, max_age):
        self.max_age = max_age


class MockSettings:
    def __init__(self, max_age):
        self.cookie = MockCookieConfig(max_age)
        self.secret_key = 'test-secret'


def test_sign_and_extract_user_id():
    """
    Tests that a user ID can be signed and then extracted successfully.
    """
    user_id = 123
    with patch('src.app.app_routes.auth.cookie.settings', MockSettings(max_age=3600)):
        token = sign_user_id(user_id)
        extracted_user_id = extract_user_id(token)
        assert extracted_user_id == user_id


def test_extract_user_id_invalid_token():
    """
    Tests that an invalid token returns None.
    """
    with patch('src.app.app_routes.auth.cookie.settings', MockSettings(max_age=3600)):
        extracted_user_id = extract_user_id("invalid-token")
        assert extracted_user_id is None


def test_extract_user_id_expired_token():
    """
    Tests that an expired token returns None.
    """
    user_id = 123
    with patch('src.app.app_routes.auth.cookie.settings', MockSettings(max_age=-1)):
        token = sign_user_id(user_id)
        # Sleep to ensure the token expires
        time.sleep(1)
        extracted_user_id = extract_user_id(token)
        assert extracted_user_id is None


def test_sign_and_verify_state_token():
    """
    Tests that a state token can be signed and then verified successfully.
    """
    state_nonce = "some-random-string"
    with patch('src.app.app_routes.auth.cookie.settings', MockSettings(max_age=3600)):
        token = sign_state_token(state_nonce)
        verified_nonce = verify_state_token(token)
        assert verified_nonce == state_nonce


def test_verify_state_token_invalid_token():
    """
    Tests that an invalid state token returns None.
    """
    with patch('src.app.app_routes.auth.cookie.settings', MockSettings(max_age=3600)):
        verified_nonce = verify_state_token("invalid-token")
        assert verified_nonce is None


def test_verify_state_token_expired_token():
    """
    Tests that an expired state token returns None.
    """
    state_nonce = "some-random-string"
    with patch('src.app.app_routes.auth.cookie.settings', MockSettings(max_age=-1)):
        token = sign_state_token(state_nonce)
        # Sleep to ensure the token expires
        time.sleep(1)
        verified_nonce = verify_state_token(token)
        assert verified_nonce is None
