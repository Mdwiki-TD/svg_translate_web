from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g, session

from src.main_app.services.users_service import (
    _resolve_user_id,
    current_user,
)

from src.main_app.db.user_tokens import UserTokenRecord


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    return app


def test_resolve_user_id(app):
    with app.test_request_context():
        session["uid"] = 123
        assert _resolve_user_id() == 123

        session["uid"] = "456"
        assert _resolve_user_id() == 456

        session.pop("uid", None)
        assert _resolve_user_id() is None

        session["uid"] = "invalid"
        assert _resolve_user_id() is None


@patch("src.main_app.services.users_service.get_user_token")
@patch("src.main_app.services.users_service.extract_user_id")
@patch("src.main_app.services.users_service.settings")
def test_current_user(mock_settings, mock_extract, mock_get_token, app):
    mock_settings.cookie.name = "test_cookie"

    mock_user = UserTokenRecord(user_id=1, username="testuser", access_token=b"", access_secret=b"")
    mock_get_token.return_value = mock_user

    with app.test_request_context():
        g._current_user = mock_user
        assert current_user() == mock_user
        del g._current_user

        session["uid"] = 1
        assert current_user() == mock_user
        assert g._current_user == mock_user
        del g._current_user
        session.clear()

        mock_extract.return_value = 1
        with app.test_request_context(environ_base={"HTTP_COOKIE": "test_cookie=signed_value"}):
            assert current_user() == mock_user
            assert session["uid"] == 1
            assert g._current_user == mock_user

        mock_extract.return_value = None
        session.clear()
        if hasattr(g, "_current_user"):
            del g._current_user
        assert current_user() is None

        mock_get_token.return_value = None
        session["uid"] = 999
        assert current_user() is None

        mock_get_token.return_value = mock_user
        session["uid"] = 1
        session["username"] = "oldname"
        if hasattr(g, "_current_user"):
            del g._current_user
        current_user()
        assert session["username"] == "testuser"
