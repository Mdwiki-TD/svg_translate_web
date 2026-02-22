import pytest
from flask import Flask, session, g, url_for
from unittest.mock import MagicMock, patch
from src.main_app.users.current import (
    CurrentUser,
    _resolve_user_id,
    current_user,
    oauth_required,
    context_user
)
from src.main_app.users.store import UserTokenRecord

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

@patch("src.app.users.current.get_user_token")
@patch("src.app.users.current.extract_user_id")
@patch("src.app.users.current.settings")
def test_current_user(mock_settings, mock_extract, mock_get_token, app):
    mock_settings.cookie.name = "test_cookie"

    # Mock user record
    mock_user = UserTokenRecord(
        user_id=1, username="testuser", access_token=b"", access_secret=b""
    )
    mock_get_token.return_value = mock_user

    with app.test_request_context():
        # 1. Cached in g
        g._current_user = mock_user
        assert current_user() == mock_user
        del g._current_user # Reset

        # 2. In Session
        session["uid"] = 1
        assert current_user() == mock_user
        assert g._current_user == mock_user
        del g._current_user
        session.clear()

        # 3. In Cookie
        mock_extract.return_value = 1
        # Create a request with the cookie
        with app.test_request_context(environ_base={'HTTP_COOKIE': 'test_cookie=signed_value'}):
             assert current_user() == mock_user
             assert session["uid"] == 1
             assert g._current_user == mock_user

        # 4. No session, no cookie
        mock_extract.return_value = None
        session.clear()
        if hasattr(g, "_current_user"): del g._current_user
        assert current_user() is None

        # 5. User in session but get_user_token returns None
        mock_get_token.return_value = None
        session["uid"] = 999
        assert current_user() is None

        # 6. Username update
        mock_get_token.return_value = mock_user # Reset to valid user
        session["uid"] = 1
        session["username"] = "oldname"
        if hasattr(g, "_current_user"): del g._current_user
        current_user()
        assert session["username"] == "testuser"

@patch("src.app.users.current.current_user")
@patch("src.app.users.current.settings")
def test_oauth_required(mock_settings, mock_current_user, app):
    mock_settings.use_mw_oauth = True

    # Mock view function
    view = MagicMock(return_value="ok")
    decorated = oauth_required(view)

    with app.test_request_context("/protected"):
        # Register a dummy login route to avoid BuildError
        app.add_url_rule('/login', endpoint='auth.login')

        # Case 1: Authenticated
        mock_current_user.return_value = MagicMock()
        assert decorated() == "ok"
        view.assert_called()

        # Case 2: Unauthenticated
        mock_current_user.return_value = None
        resp = decorated()
        assert resp.status_code == 302 # Redirect
        assert session.get("post_login_redirect") == "http://localhost/protected"

        # Case 3: OAuth disabled
        mock_settings.use_mw_oauth = False
        mock_current_user.return_value = None
        view.reset_mock()
        assert decorated() == "ok"
        view.assert_called()

@patch("src.app.users.current.active_coordinators")
@patch("src.app.users.current.current_user")
def test_context_user(mock_current_user, mock_active_coordinators):
    # Case 1: User is admin
    user = MagicMock(username="admin")
    mock_current_user.return_value = user
    mock_active_coordinators.return_value = ["admin"]

    ctx = context_user()
    assert ctx["current_user"] == user
    assert ctx["is_authenticated"] is True
    assert ctx["is_admin"] is True
    assert ctx["username"] == "admin"

    # Case 2: User is not admin
    mock_active_coordinators.return_value = ["other"]
    ctx = context_user()
    assert ctx["is_admin"] is False

    # Case 3: No user
    mock_current_user.return_value = None
    ctx = context_user()
    assert ctx["current_user"] is None
    assert ctx["is_authenticated"] is False
    assert ctx["is_admin"] is False
    assert ctx["username"] is None

def test_CurrentUser():
    # Just simple data class test
    u = CurrentUser(user_id="1", username="foo")
    assert u.user_id == "1"
    assert u.username == "foo"
