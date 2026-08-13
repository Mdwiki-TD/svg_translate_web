"""
Authentication utilities and decorators for routes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flask import redirect, request, session, url_for

from ...shared.auth.utils import get_current_user

FuncType = TypeVar("FuncType", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def oauth_required(func: FuncType) -> FuncType:  # noqa: UP047
    """Decorator that requires a full OAuth credential bundle."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        # Check g._current_user which was populated by set_logged_in_user
        user = get_current_user()
        if not user:
            session["post_login_redirect"] = request.url
            return redirect(url_for("auth.login"))

        return func(*args, **kwargs)

    return cast(FuncType, wrapper)


__all__ = [
    "oauth_required",
]
