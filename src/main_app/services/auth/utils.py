"""
Authentication utilities and decorators for routes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from flask import g, request, session

from ...config import settings
from ..core.cookies import extract_user_id
from .current_user import CurrentUser
from .token_manager import TokenManager

FuncType = TypeVar("FuncType", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def get_current_user() -> CurrentUser | None:
    """Return the :class:`CurrentUser` populated by ``set_logged_in_user``.

    Returns ``None`` when no user is authenticated. The before_request hook
    always sets ``g._current_user`` (to ``None`` for anonymous visitors), so
    this is the single source of truth during a request.
    """
    return getattr(g, "_current_user", None)


def _resolve_user_id(uid) -> int | None:
    if isinstance(uid, int):
        return uid
    try:
        return int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return None


def _get_user_id() -> None | int:
    """Extract and validate user_id from session or cookie."""
    # 1. Try to resolve user_id from session
    user_id = session.get("uid")

    # 2. Fallback to cookie if session is empty
    if user_id is None:
        signed = request.cookies.get(settings.cookie.name)
        if signed:
            user_id = extract_user_id(signed)
            if user_id is not None:
                session["uid"] = user_id

    # 3. Resolve user_id and clean up session if invalid
    if user_id is not None:
        user_id = _resolve_user_id(user_id)
        if user_id is None:
            session.pop("uid", None)
            session.pop("username", None)

    return user_id


def _build_current_user(user_id) -> None | CurrentUser:
    """
    Fetch user from Service Layer and hydrate session/g context.
    """
    if user_id is None:
        return None

    user = TokenManager().get_authenticated_user(user_id)

    if user and session.get("username") != user.username:
        session["username"] = user.username

    return user


def set_logged_in_user() -> None:
    """Build a :class:`CurrentUser` from the session and store it in ``g``.

    Called once per request by ``before_app_request``. Anonymous sessions
    (no ``username`` in the session) get ``g._current_user = None`` and incur
    no database work. Authenticated sessions are hydrated from ``UserRecord``
    (id + admin flag) and the decrypted OAuth token pair.
    """
    if hasattr(g, "_current_user"):
        return
    user_id = _get_user_id()
    g._current_user = _build_current_user(user_id)


__all__ = [
    "set_logged_in_user",
]
