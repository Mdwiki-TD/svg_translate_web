"""Helpers for signing and verifying user identification cookies and state tokens."""

from __future__ import annotations

import logging

from itsdangerous import BadSignature, BadTimeSignature, URLSafeTimedSerializer

from ....config import get_settings

logger = logging.getLogger(__name__)


def _build_serializer(purpose: str) -> URLSafeTimedSerializer:
    """Create a serializer whose salt is scoped to a single purpose."""
    settings = get_settings()
    return URLSafeTimedSerializer(
        settings.security.secret_key,
        salt=f"{settings.security.salt}-{purpose}",
    )


class SignedTokenService:
    """Sign and verify user-id tokens and OAuth state tokens."""

    def __init__(
        self,
        uid_serializer: URLSafeTimedSerializer | None = None,
        state_serializer: URLSafeTimedSerializer | None = None,
        max_age: int | None = None,
    ) -> None:
        # Separate salts keep a token of one kind from validating as the other
        self.uid_serializer = uid_serializer or _build_serializer("uid")
        self.state_serializer = state_serializer or _build_serializer("oauth-state")

        self.settings = get_settings()
        self.max_age = max_age if max_age is not None else self.settings.cookie.max_age

    # ---- user id tokens ----

    def dump_uid(self, data):
        """Serialize raw data with the user id serializer."""
        return self.uid_serializer.dumps(data)

    def sign_user_id(self, user_id: int) -> str:
        """Generate a signed payload for the given user id."""
        logger.debug("Signing user_id: %s", user_id)
        return self.dump_uid({"uid": int(user_id)})

    def extract_user_id(self, token: str) -> int | None:
        """Validate and decode a signed user id token."""
        logger.debug("Extracting user_id from token")
        try:
            data = self.uid_serializer.loads(token, max_age=self.max_age)
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

    # ---- OAuth state tokens ----

    def dump_state(self, data):
        """Serialize raw data with the OAuth state serializer."""
        return self.state_serializer.dumps(data)

    def sign_state_token(self, state_nonce: str) -> str:
        """Sign and serialize an OAuth state nonce."""
        logger.debug("Signing state nonce")
        return self.dump_state({"nonce": state_nonce})

    def verify_state_token(self, token: str) -> str | None:
        """Validate a signed OAuth state token and return the embedded nonce."""
        logger.debug("Verifying state token")
        try:
            data = self.state_serializer.loads(token, max_age=self.max_age)
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
    "SignedTokenService",
]
