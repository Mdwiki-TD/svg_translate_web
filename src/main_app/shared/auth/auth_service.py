"""OAuth callback business logic extracted from auth/routes.py."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any, Tuple

from .auth_users_service import AuthUserService
from .mwoauth_handshake import complete_login

logger = logging.getLogger(__name__)


class OAuthCallbackError(Exception):
    """Raised when a step of the OAuth callback fails."""

    def __init__(self, message: str, *, flash_category: str = "danger") -> None:
        super().__init__(message)
        self.flash_category = flash_category


def extract_token_credentials(access_token: Any) -> Tuple[str, str]:
    """Extract key/secret from an OAuth access token object."""
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

    user_record = AuthUserService.save_and_get_user(
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
]
