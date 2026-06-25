"""
Authentication utilities and decorators for routes.
"""

from __future__ import annotations

import logging
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import flash, g, redirect, request, session, url_for

from ...config import settings
from ...shared.auth.auth_users_service import AuthUserService
from ...shared.core.cookies import extract_user_id

FuncType = TypeVar("FuncType", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def load_user():
    user = getattr(g, "_current_user", None)
    return user


def _resolve_user_id(uid) -> int | None:
    if isinstance(uid, int):
        return uid
    try:
        return int(uid) if uid is not None else None
    except (TypeError, ValueError):
        return None


def load_logged_in_user() -> None:
    """Automatically load the user from session or cookie before each request.

    Populates g._current_user for the lifecycle of the request.
    """
    if hasattr(g, "_current_user"):
        return

    # 1. Try to resolve user_id from session
    user_id = session.get("uid")

    # 2. Fallback to cookie if session is empty
    if user_id is None:
        signed = request.cookies.get(settings.cookie.name)
        if signed:
            user_id = extract_user_id(signed)
            if user_id is not None:
                session["uid"] = user_id

    # 3. Fetch from Service Layer if user_id exists
    if user_id is not None:
        user_id = _resolve_user_id(user_id)
        # Short-circuit when _resolve_user_id() returns None
        if user_id is None:
            session.pop("uid", None)
            session.pop("username", None)
            g._current_user = None
            return

        user = AuthUserService.get_authenticated_user(user_id)
        g._current_user = user
        if user and session.get("username") != user.username:
            session["username"] = user.username
    else:
        g._current_user = None


def oauth_required(func: FuncType) -> FuncType:  # noqa: UP047
    """Decorator that requires a full OAuth credential bundle."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        # Check g._current_user which was populated by load_logged_in_user
        user = load_user()
        if not user:
            session["post_login_redirect"] = request.url
            return redirect(url_for("auth.login"))

        return func(*args, **kwargs)

    return cast(FuncType, wrapper)


def user_login_required(func: FuncType) -> FuncType:  # noqa: UP047
    """
    Decorator that requires user login
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        user = load_user()
        if not user:
            # Get the page the user came from, or default to the home page
            next_page = "/"
            if request.referrer and request.referrer.startswith(request.host_url):
                next_page = request.referrer
            # Return him to previous page with flash msg
            flash("You must be logged in.", "danger")
            return redirect(next_page)

        return func(*args, **kwargs)

    return cast(FuncType, wrapper)


__all__ = [
    "user_login_required",
    "load_logged_in_user",
    "oauth_required",
]
