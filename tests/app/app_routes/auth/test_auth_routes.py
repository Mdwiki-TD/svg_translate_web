"""
Tests for authentication routes.
"""
from unittest.mock import MagicMock, patch

from flask import Flask, g, session
import pytest

from src.app.app_routes.auth.routes import bp_auth, login_required


@pytest.fixture
def app():
    """Create a Flask app instance for testing."""
    app = Flask(__name__)
    app.secret_key = 'test-secret'
    app.register_blueprint(bp_auth, url_prefix='/auth')
    app.add_url_rule('/', 'main.index', lambda: 'Home Page')
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()


def test_login_required_not_logged_in(app, client):
    """
    Tests that a user who is not logged in is redirected.
    """
    @app.route('/protected')
    @login_required
    def protected_route():
        return "You should not see this"

    response = client.get('/protected')
    assert response.status_code == 302
    assert response.headers['Location'] == '/?error=login-required'


def test_login_required_logged_in(app, client):
    """
    Tests that a logged-in user can access the protected route.
    """
    @app.route('/protected')
    @login_required
    def protected_route():
        return "Welcome"

    with app.test_request_context('/protected'):
        g.is_authenticated = True
        response = protected_route()
        assert response == "Welcome"


@patch('src.app.app_routes.auth.routes.settings')
@patch('src.app.app_routes.auth.routes.login_rate_limiter')
def test_login_oauth_disabled(mock_rate_limiter, mock_settings, client):
    """
    Tests that login redirects if OAuth is disabled.
    """
    mock_settings.use_mw_oauth = False
    response = client.get('/auth/login')
    assert response.status_code == 302
    assert response.headers['Location'] == '/?error=oauth-disabled'


@patch('src.app.app_routes.auth.routes.settings')
@patch('src.app.app_routes.auth.routes.login_rate_limiter')
def test_login_rate_limited(mock_rate_limiter, mock_settings, client):
    """
    Tests that login redirects if the rate limit is exceeded.
    """
    mock_settings.use_mw_oauth = True
    mock_rate_limiter.allow.return_value = False
    mock_rate_limiter.try_after.return_value = MagicMock(total_seconds=lambda: 60)
    response = client.get('/auth/login')
    assert response.status_code == 302
    assert 'Too+many+login+attempts' in response.headers['Location']


class MockRequestToken:
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def __iter__(self):
        yield self.key
        yield self.secret


@patch('src.app.app_routes.auth.routes.settings')
@patch('src.app.app_routes.auth.routes.start_login')
@patch('src.app.app_routes.auth.routes.login_rate_limiter')
@patch('src.app.app_routes.auth.routes.secrets.token_urlsafe')
def test_login_success(mock_token_urlsafe, mock_rate_limiter, mock_start_login, mock_settings, client):
    """
    Tests a successful login initiation.
    """
    mock_settings.use_mw_oauth = True
    mock_settings.STATE_SESSION_KEY = 'oauth_state_nonce'
    mock_settings.REQUEST_TOKEN_SESSION_KEY = 'request_token_key'
    mock_rate_limiter.allow.return_value = True
    mock_start_login.return_value = ('https://oauth.example.com', MockRequestToken('token', 'secret'))
    mock_token_urlsafe.return_value = 'test-nonce'

    response = client.get('/auth/login')
    assert response.status_code == 302
    assert response.headers['Location'] == 'https://oauth.example.com'
    with client.session_transaction() as sess:
        assert sess['oauth_state_nonce'] == 'test-nonce'
        assert sess['request_token_key'] == ['token', 'secret']


@patch('src.app.app_routes.auth.routes.settings')
@patch('src.app.app_routes.auth.routes.callback_rate_limiter')
@patch('src.app.app_routes.auth.routes.verify_state_token')
@patch('src.app.app_routes.auth.routes._load_request_token')
@patch('src.app.app_routes.auth.routes.complete_login')
@patch('src.app.app_routes.auth.routes.upsert_user_token')
@patch('src.app.app_routes.auth.routes.sign_user_id')
def test_callback_success(
    mock_sign_user_id, mock_upsert, mock_complete_login, mock_load_token,
    mock_verify_token, mock_rate_limiter, mock_settings, client
):
    """
    Tests a successful callback.
    """
    mock_settings.use_mw_oauth = True
    mock_settings.STATE_SESSION_KEY = 'oauth_state_nonce'
    mock_settings.REQUEST_TOKEN_SESSION_KEY = 'request_token_key'
    mock_settings.cookie.name = 'uid_enc'
    mock_rate_limiter.allow.return_value = True
    mock_verify_token.return_value = 'test-nonce'
    mock_load_token.return_value = 'request-token'
    mock_complete_login.return_value = (('key', 'secret'), {'sub': 123, 'username': 'testuser'})
    mock_sign_user_id.return_value = 'signed-user-id'

    with client.session_transaction() as sess:
        sess[mock_settings.STATE_SESSION_KEY] = 'test-nonce'
        sess[mock_settings.REQUEST_TOKEN_SESSION_KEY] = ('token', 'secret')

    response = client.get('/auth/callback?state=test-nonce&oauth_verifier=test-verifier')
    assert response.status_code == 302
    assert response.headers['Location'] == '/'
    mock_upsert.assert_called_once()


def test_logout(client):
    """
    Tests the logout functionality.
    """
    with client:
        with client.session_transaction() as sess:
            sess['uid'] = 123
            sess['username'] = 'testuser'
        response = client.get('/auth/logout')
        assert response.status_code == 302
        assert response.headers['Location'] == '/'
    with client.session_transaction() as sess:
        assert 'uid' not in sess
        assert 'username' not in sess
