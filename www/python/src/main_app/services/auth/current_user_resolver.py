"""
Authentication utilities — session/cookie resolution and request hooks.
"""

from __future__ import annotations

import logging

from flask import g, request, session

from ...config import get_settings
from ...core.cookies.signing import SignedTokenService
from .current_user import CurrentUser
from .token_manager import TokenManager

logger = logging.getLogger(__name__)


class CurrentUserResolver:
    """Resolve the authenticated user of the current request."""

    def __init__(
        self,
        signer: SignedTokenService | None = None,
        token_manager: TokenManager | None = None,
        cookie_name: str | None = None,
    ) -> None:
        self.signer = signer or SignedTokenService()
        self.token_manager = token_manager or TokenManager()
        self.cookie_name = cookie_name or get_settings().cookie.name

    @staticmethod
    def resolve_user_id(uid) -> int | None:
        """Coerce a raw uid value to ``int``, or ``None`` if it is invalid."""
        if isinstance(uid, int):
            return uid
        try:
            return int(uid) if uid is not None else None
        except (TypeError, ValueError):
            return None

    def get_user_id(self) -> int | None:
        """Extract and validate user_id from the session or the signed cookie."""
        # 1. Try the session first
        user_id = session.get("uid")

        # 2. Fall back to the signed cookie if the session is empty
        if user_id is None:
            signed = request.cookies.get(self.cookie_name)
            if signed:
                user_id = self.signer.extract_user_id(signed)
                if user_id is not None:
                    session["uid"] = user_id

        # 3. Normalize the value and clean up the session if it is invalid
        if user_id is not None:
            user_id = self.resolve_user_id(user_id)
            if user_id is None:
                session.pop("uid", None)
                session.pop("username", None)

        return user_id

    def build_current_user(self, user_id: int | None) -> CurrentUser | None:
        """Assemble a :class:`CurrentUser` for the given user_id from the DB."""
        if user_id is None:
            return None

        record: CurrentUser | None = self.token_manager.get_authenticated_user(user_id)

        # Keep the cached username in the session in sync with the DB record
        if record and session.get("username") != record.username:
            session["username"] = record.username

        return record

    def set_logged_in_user(self) -> None:
        """Build a :class:`CurrentUser` from the session and store it in ``g``.

        Called once per request by ``before_app_request``. Anonymous sessions
        get ``g._current_user = None`` and incur no database work.
        """
        if hasattr(g, "_current_user"):
            return
        g._current_user = self.build_current_user(self.get_user_id())

    @staticmethod
    def get_current_user() -> CurrentUser | None:
        """Return the :class:`CurrentUser` populated by ``set_logged_in_user``.

        Returns ``None`` when no user is authenticated. The before_request hook
        always sets ``g._current_user`` (to ``None`` for anonymous visitors), so
        this is the single source of truth during a request.
        """
        return getattr(g, "_current_user", None)


__all__ = [
    "CurrentUserResolver",
]
