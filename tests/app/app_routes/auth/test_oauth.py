"""
Tests for OAuth handshake helpers.
"""
from unittest.mock import MagicMock, patch

import pytest
from mwoauth import ConsumerToken, Handshaker

from src.app.app_routes.auth.oauth import (
    OAuthIdentityError,
    complete_login,
    get_handshaker,
    start_login,
)


class MockOAuthConfig:
    def __init__(self, consumer_key, consumer_secret, mw_uri, user_agent):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.mw_uri = mw_uri
        self.user_agent = user_agent


@patch('src.app.app_routes.auth.oauth.settings')
def test_get_handshaker_success(mock_settings):
    """
    Tests that a Handshaker is created successfully.
    """
    mock_settings.oauth = MockOAuthConfig(
        'key', 'secret', 'https://example.com', 'agent'
    )
    handshaker = get_handshaker()
    assert isinstance(handshaker, Handshaker)
    assert isinstance(handshaker.consumer_token, ConsumerToken)
    assert handshaker.mw_uri == 'https://example.com'


@patch('src.app.app_routes.auth.oauth.settings')
def test_get_handshaker_no_config(mock_settings):
    """
    Tests that a RuntimeError is raised when OAuth is not configured.
    """
    mock_settings.oauth = None
    with pytest.raises(RuntimeError):
        get_handshaker()


@patch('src.app.app_routes.auth.oauth.get_handshaker')
def test_start_login(mock_get_handshaker):
    """
    Tests the start_login function.
    """
    mock_handshaker = MagicMock()
    mock_handshaker.initiate.return_value = ('redirect-url', 'request-token')
    mock_get_handshaker.return_value = mock_handshaker

    with patch('src.app.app_routes.auth.oauth.url_for', return_value='callback-url'):
        redirect_url, request_token = start_login('state-token')

    mock_handshaker.initiate.assert_called_once_with(callback='callback-url')
    assert redirect_url == 'redirect-url'
    assert request_token == 'request-token'


@patch('src.app.app_routes.auth.oauth.get_handshaker')
def test_complete_login_success(mock_get_handshaker):
    """
    Tests a successful completion of the login process.
    """
    mock_handshaker = MagicMock()
    mock_handshaker.complete.return_value = 'access-token'
    mock_handshaker.identify.return_value = 'identity'
    mock_get_handshaker.return_value = mock_handshaker

    access_token, identity = complete_login('request-token', 'query-string')

    mock_handshaker.complete.assert_called_once_with('request-token', 'query-string')
    mock_handshaker.identify.assert_called_once_with('access-token')
    assert access_token == 'access-token'
    assert identity == 'identity'


@patch('src.app.app_routes.auth.oauth.get_handshaker')
def test_complete_login_identity_error(mock_get_handshaker):
    """
    Tests that an OAuthIdentityError is raised on identity failure.
    """
    mock_handshaker = MagicMock()
    mock_handshaker.complete.return_value = 'access-token'
    mock_handshaker.identify.side_effect = Exception("Identity failure")
    mock_get_handshaker.return_value = mock_handshaker

    with pytest.raises(OAuthIdentityError):
        complete_login('request-token', 'query-string')


def test_oauth_identity_error():
    """
    Tests that OAuthIdentityError can be raised and caught.
    """
    with pytest.raises(OAuthIdentityError):
        raise OAuthIdentityError("Test error")
