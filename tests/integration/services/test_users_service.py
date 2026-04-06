from unittest.mock import patch

import pytest
extra_import_from_tests_conftest = False
try:
    from tests.conftest import UserTokenRecord
    extra_import_from_tests_conftest = True
except ImportError:
    from src.main_app.db.user_tokens import UserTokenRecord

from flask import Flask, g, session

from src.main_app.services.users_service import (
    _resolve_user_id,
    current_user,
)

@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test_secret"
    return app


def test_resolve_user_id(app):
    with app.test_request_context():
        # Case 1: int
        session["uid"] = 123
        assert _resolve_user_id() == 123

        # Case 2: str
        session["uid"] = "456"
        assert _resolve_user_id() == 456

        # Case 3: None
        session.pop("uid", None)
        assert _resolve_user_id() is None

        # Case 4: Invalid
        session["uid"] = "invalid"
        assert _resolve_user_id() is None


@patch("src.main_app.services.users_service.get_user_token")
@patch("src.main_app.services.users_service.extract_user_id")
@patch("src.main_app.services.users_service.settings")
def test_current_user(mock_settings, mock_extract, mock_get_token, app):
    mock_settings.cookie.name = "test_cookie"

    # Mock user record
    mock_user = UserTokenRecord(user_id=1, username="testuser", access_token=b"", access_secret=b"")
    mock_get_token.return_value = mock_user

    with app.test_request_context():
        # 1. Cached in g
        g._current_user = mock_user
        assert current_user() == mock_user
        del g._current_user  # Reset

        # 2. In Session
        session["uid"] = 1
        assert current_user() == mock_user
        assert g._current_user == mock_user
        del g._current_user
        session.clear()

        # 3. In Cookie
        mock_extract.return_value = 1
        # Create a request with the cookie
        with app.test_request_context(environ_base={"HTTP_COOKIE": "test_cookie=signed_value"}):
            assert current_user() == mock_user
            assert session["uid"] == 1
            assert g._current_user == mock_user

        # 4. No session, no cookie
        mock_extract.return_value = None
        session.clear()
        if hasattr(g, "_current_user"):
            del g._current_user
        assert current_user() is None

        # 5. User in session but get_user_token returns None
        mock_get_token.return_value = None
        session["uid"] = 999
        assert current_user() is None

        # 6. Username update
        mock_get_token.return_value = mock_user  # Reset to valid user
        session["uid"] = 1
        session["username"] = "oldname"
        if hasattr(g, "_current_user"):
            del g._current_user
        current_user()
        assert session["username"] == "testuser"
