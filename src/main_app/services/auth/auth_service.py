"""
OAuthService — handles the mwoauth handshake with Meta-Wiki.
"""

from __future__ import annotations

import logging
from typing import Any

from mwoauth import AccessToken, ConsumerToken, RequestToken
from mwoauth.handshaker import Handshaker

from ...config import settings
from .auth_exceptions import IDENTITY_ERROR_MESSAGE, OAuthCallbackError, OAuthIdentityError

logger = logging.getLogger(__name__)


class OAuthService:
    """Manages the OAuth 1.0a authorization flow against Meta-Wiki.

    Responsibilities:
    - Build the authorization URL to redirect the user to.
    - Exchange the callback verifier for an access token.
    """

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        oauth_mwuri: str,
    ) -> None:
        """Initialize the OAuth service."""
        self._mw_uri = oauth_mwuri
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret

    def get_handshaker(self) -> Handshaker:
        if not settings.oauth:
            raise RuntimeError("MediaWiki OAuth configuration is incomplete")

        consumer_token = ConsumerToken(
            settings.oauth.consumer_key,
            settings.oauth.consumer_secret,
        )
        handshaker = Handshaker(
            mw_uri=settings.oauth.mw_uri,
            consumer_token=consumer_token,
            user_agent=settings.other.user_agent,
        )
        return handshaker

    def create_authorization_url(self, callback_url: str) -> tuple[str, str, str]:
        """
        Step 1: Obtain a request token and build the redirect URL.

        Returns:
            (authorization_url, oauth_token, oauth_token_secret)
        """
        logger.debug("Starting OAuth login with state_token")

        handshaker = self.get_handshaker()

        authorization_url, request_token = handshaker.initiate(callback=callback_url)

        logger.info("OAuth login initiated, redirecting to: %s", authorization_url)

        return (
            authorization_url,
            request_token.key,
            request_token.secret,
        )

    def fetch_access_token(
        self,
        query_string: str,
        oauth_token: str,
        oauth_token_secret: str,
    ) -> AccessToken:
        """
        Step 2: Exchange the callback for a permanent access token.

        Args:
            query_string:
            oauth_token: The request token from step 1.
            oauth_token_secret: The request token secret from step 1.

        Returns:
            AccessToken object.
        """
        logger.debug("Completing OAuth login with query_string")
        handshaker = self.get_handshaker()

        request_token = RequestToken(oauth_token, oauth_token_secret)

        access_token: AccessToken = handshaker.complete(request_token, query_string)

        return access_token

    def identify(self, access_token: AccessToken) -> dict[str, Any]:
        """
        Fetch the authenticated user's identity from Meta-Wiki.

        identity example: for references: {
            "iss": "https://meta.wikimedia.org",
            "sub": "4327653",
            "username": "username",
            "editcount": 1182,
            "email_verified": true, "confirmed_email": true,
            "blocked": false,
            "registered": "20110101133631",
            "groups": [ "autopatrolled", "*", "user", "autoconfirmed" ],
            "rights": [ "read", "edit" ],
            "grants": [ "basic", "editpage", "createeditmovepage", "uploadfile", "uploadeditmovefile", "editmywatchlist" ],
            "nonce": ""
        }

        Returns:
            dict with at least ``username`` key.
        """
        handshaker = self.get_handshaker()
        try:
            identity: dict[str, Any] = handshaker.identify(access_token)
            logger.info("OAuth identity verified: %s", identity.get("username") or identity.get("name"))
        except Exception as exc:
            logger.exception("OAuth identity verification failed")
            raise OAuthIdentityError(IDENTITY_ERROR_MESSAGE, original_exception=exc) from exc

        identity_dict: dict[str, Any] = identity if isinstance(identity, dict) else {}

        username = identity_dict.get("username") or identity_dict.get("name")
        if not username:
            raise OAuthCallbackError("Missing username")

        return identity_dict


__all__ = [
    "OAuthService",
]
