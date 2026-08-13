"""OAuth callback business logic extracted from auth/routes.py."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import mwoauth
from flask import url_for
from mwoauth import AccessToken
from mwoauth.handshaker import Handshaker

from ...config import settings
from .auth_users_service import AuthUserService

logger = logging.getLogger(__name__)

IDENTITY_ERROR_MESSAGE = "We couldn't verify your MediaWiki identity. Please try again."


class OAuthCallbackError(Exception):
    """Raised when a step of the OAuth callback fails."""

    def __init__(self, message: str, *, flash_category: str = "danger") -> None:
        super().__init__(message)
        self.flash_category = flash_category


class OAuthIdentityError(Exception):
    """Raised when MediaWiki OAuth identity verification fails."""

    def __init__(self, message: str, *, original_exception: Exception | None = None) -> None:
        super().__init__(message)
        self.original_exception = original_exception


def get_handshaker() -> Handshaker:
    if not settings.oauth:
        raise RuntimeError("MediaWiki OAuth configuration is incomplete")

    consumer_token = mwoauth.ConsumerToken(settings.oauth.consumer_key, settings.oauth.consumer_secret)
    return mwoauth.Handshaker(
        settings.oauth.mw_uri,
        consumer_token=consumer_token,
        user_agent=settings.other.user_agent,
    )


def start_login(state_token: str) -> tuple[str, Any]:
    """Begin the OAuth login process and return the redirect URL and request token."""
    logger.debug("Starting OAuth login with state_token")
    callback_url = url_for("auth.callback", _external=True, state=state_token)
    handshaker = get_handshaker()
    redirect_url, request_token = handshaker.initiate(callback=callback_url)
    logger.info("OAuth login initiated, redirecting to: %s", redirect_url)

    return redirect_url, request_token


def complete_login(request_token: object, query_string: str) -> tuple[AccessToken | Any, dict[str, Any]]:
    """Complete the OAuth login flow and return the access token and user identity."""
    logger.debug("Completing OAuth login with query_string")
    handshaker = get_handshaker()
    access_token: AccessToken = handshaker.complete(request_token, query_string)
    logger.info("OAuth access token obtained")
    try:
        identity: dict[str, Any] = handshaker.identify(access_token)
        logger.info("OAuth identity verified: %s", identity.get("username") or identity.get("name"))
    except Exception as exc:
        logger.exception("OAuth identity verification failed")
        raise OAuthIdentityError(IDENTITY_ERROR_MESSAGE, original_exception=exc) from exc
    return access_token, identity


def extract_token_credentials(access_token: AccessToken | Any) -> tuple[str, str]:
    """Extract key/secret from an OAuth access token object."""
    if not access_token:
        raise OAuthCallbackError("Missing OAuth credentials")

    token_key = getattr(access_token, "key", None)
    token_secret = getattr(access_token, "secret", None)

    if (
        not (token_key and token_secret)
        and isinstance(access_token, Sequence)
        and not isinstance(access_token, str | bytes | bytearray)
    ):
        if len(access_token) >= 2:
            token_key = access_token[0]
            token_secret = access_token[1]

    if not (token_key and token_secret):
        raise OAuthCallbackError("Missing OAuth credentials")

    return str(token_key), str(token_secret)


def complete_oauth_callback(request_token: Any, query_string: str) -> Any:
    """Complete the OAuth handshake and persist credentials.

    Returns:
        (user_id, username, user_record)

    Raises:
        OAuthIdentityError: If identity verification fails.
        OAuthCallbackError: If token extraction or user persistence fails.

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
    """
    access_token, identity = complete_login(request_token, query_string)
    token_key, token_secret = extract_token_credentials(access_token)

    identity_dict: dict[str, Any] = identity if isinstance(identity, dict) else {}
    username = identity_dict.get("username") or identity_dict.get("name")
    if not username:
        raise OAuthCallbackError("Missing username")

    user_record = AuthUserService().save_and_get_user(
        username=username,
        access_key=token_key,
        access_secret=token_secret,
    )

    if not user_record:
        raise OAuthCallbackError("Failed to process user credentials")

    return user_record


__all__ = [
    "OAuthCallbackError",
    "complete_oauth_callback",
    "extract_token_credentials",
    "OAuthIdentityError",
    "get_handshaker",
    "start_login",
    "complete_login",
]
