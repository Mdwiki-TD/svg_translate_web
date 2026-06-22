"""Helpers for performing the MediaWiki OAuth handshake."""

from __future__ import annotations

import logging
from typing import Any, Tuple

import mwoauth
from flask import url_for
from mwoauth.handshaker import Handshaker

from ...config import settings

logger = logging.getLogger(__name__)

IDENTITY_ERROR_MESSAGE = "We couldn't verify your MediaWiki identity. Please try again."


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


def start_login(state_token: str) -> Tuple[str, object]:
    """Begin the OAuth login process and return the redirect URL and request token."""
    logger.debug("Starting OAuth login with state_token")
    callback_url = url_for("auth.callback", _external=True, state=state_token)
    handshaker = get_handshaker()
    redirect_url, request_token = handshaker.initiate(callback=callback_url)
    logger.info("OAuth login initiated, redirecting to: %s", redirect_url)

    return redirect_url, request_token


def complete_login(request_token: object, query_string: str) -> Tuple[str, dict[str, Any]]:
    """Complete the OAuth login flow and return the access token and user identity."""
    logger.debug("Completing OAuth login with query_string")
    handshaker = get_handshaker()
    access_token: mwoauth.AccessToken = handshaker.complete(request_token, query_string)
    logger.info("OAuth access token obtained")
    try:
        identity: dict[str, Any] = handshaker.identify(access_token)
        logger.info("OAuth identity verified: %s", identity.get("username") or identity.get("name"))
    except Exception as exc:
        logger.exception("OAuth identity verification failed")
        raise OAuthIdentityError(IDENTITY_ERROR_MESSAGE, original_exception=exc) from exc
    return access_token, identity


__all__ = [
    "OAuthIdentityError",
    "get_handshaker",
    "start_login",
    "complete_login",
]
