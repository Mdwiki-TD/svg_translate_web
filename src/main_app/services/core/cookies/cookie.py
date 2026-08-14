"""Helpers for signing and verifying user identification cookies and state tokens."""

from __future__ import annotations

import logging

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer

from ....config import settings

logger = logging.getLogger(__name__)

_serializer = URLSafeTimedSerializer(settings.security.secret_key, salt=f"{settings.security.salt}-uid")

_state_serializer = URLSafeTimedSerializer(settings.security.secret_key, salt=f"{settings.security.salt}-oauth-state")


def sign_user_id(user_id: int) -> str:
    """Generate a signed payload for the given user id."""
    logger.debug("Signing user_id: %s", user_id)
    return _serializer.dumps({"uid": int(user_id)})


def extract_user_id(token: str) -> int | None:
    """Validate and decode a signed user id token."""
    logger.debug("Extracting user_id from token")
    try:
        data = _serializer.loads(token, max_age=settings.cookie.max_age)
    except (BadSignature, BadTimeSignature):
        logger.exception("Failed to extract user_id: invalid or expired token")
        return None
    try:
        uid = int(data.get("uid"))
        logger.debug("Extracted user_id: %s", uid)
        return uid
    except (TypeError, ValueError):
        logger.exception("Failed to extract user_id: invalid uid in data")
        return None


def sign_state_token(state_nonce: str) -> str:
    """Sign and serialize an OAuth state nonce."""
    logger.debug("Signing state nonce")
    return _state_serializer.dumps({"nonce": state_nonce})


def verify_state_token(token: str) -> str | None:
    """Validate a signed OAuth state token and return the embedded nonce."""
    logger.debug("Verifying state token")
    try:
        data = _state_serializer.loads(token, max_age=settings.cookie.max_age)
    except (BadSignature, BadTimeSignature):
        logger.exception("Failed to verify state token: invalid or expired")
        return None
    nonce = data.get("nonce")
    if not isinstance(nonce, str):
        logger.warning("Failed to verify state token: nonce not a string")
        return None
    logger.debug("State token verified successfully")
    return nonce


__all__ = [
    "sign_user_id",
    "extract_user_id",
    "sign_state_token",
    "verify_state_token",
]
