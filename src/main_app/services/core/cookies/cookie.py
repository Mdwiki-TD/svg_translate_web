"""Helpers for signing and verifying user identification cookies and state tokens."""

from __future__ import annotations

import logging

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer

from ....config import get_settings

logger = logging.getLogger(__name__)


class SignedTokenService:
    """Sign and verify user-id tokens and OAuth state tokens."""

    def __init__(
        self,
        uid_serializer: URLSafeTimedSerializer | None = None,
        state_serializer: URLSafeTimedSerializer | None = None,
        max_age: int | None = None,
    ) -> None:
        self.settings = get_settings()
        self.uid_serializer = uid_serializer or URLSafeTimedSerializer(
            self.settings.security.secret_key,
            salt=f"{self.settings.security.salt}-uid",
        )

        self.state_serializer = state_serializer or URLSafeTimedSerializer(
            self.settings.security.secret_key,
            salt=f"{self.settings.security.salt}-oauth-state",
        )
        self._max_age = self.settings.cookie.max_age if max_age is None else max_age

    def sign_user_id(self, user_id: int) -> str:
        """Generate a signed payload for the given user id."""
        logger.debug("Signing user_id: %s", user_id)
        return self.uid_serializer.dumps({"uid": int(user_id)})

    def extract_user_id(self, token: str) -> int | None:
        """Validate and decode a signed user id token."""
        logger.debug("Extracting user_id from token")
        try:
            data = self.uid_serializer.loads(token, max_age=self._max_age)
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

    def sign_state_token(self, state_nonce: str) -> str:
        """Sign and serialize an OAuth state nonce."""
        logger.debug("Signing state nonce")
        return self.state_serializer.dumps({"nonce": state_nonce})

    def verify_state_token(self, token: str) -> str | None:
        """Validate a signed OAuth state token and return the embedded nonce."""
        logger.debug("Verifying state token")
        try:
            data = self.state_serializer.loads(token, max_age=self._max_age)
        except (BadSignature, BadTimeSignature):
            logger.exception("Failed to verify state token: invalid or expired")
            return None
        nonce = data.get("nonce")
        if not isinstance(nonce, str):
            logger.warning("Failed to verify state token: nonce not a string")
            return None
        logger.debug("State token verified successfully")
        return nonce


# --- Legacy compatibility layer: thin wrappers, no logic of their own ---

_default_service = SignedTokenService()


def sign_user_id(user_id: int) -> str:
    """Generate a signed payload for the given user id."""
    return _default_service.sign_user_id(user_id)


def extract_user_id(token: str) -> int | None:
    """Validate and decode a signed user id token."""
    return _default_service.extract_user_id(token)


def sign_state_token(state_nonce: str) -> str:
    """Sign and serialize an OAuth state nonce."""
    return _default_service.sign_state_token(state_nonce)


def verify_state_token(token: str) -> str | None:
    """Validate a signed OAuth state token and return the embedded nonce."""
    return _default_service.verify_state_token(token)


__all__ = [
    "SignedTokenService",
    "sign_user_id",
    "extract_user_id",
    "sign_state_token",
    "verify_state_token",
]
