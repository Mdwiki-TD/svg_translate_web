"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import TypeVar, cast

from flask import (
    abort,
    redirect,
    url_for,
)
from flask.typing import ResponseReturnValue

from ..public.auth.utils import load_user
from ..shared.auth.current_user import CurrentUser

logger = logging.getLogger(__name__)

FuncType = TypeVar("FuncType", bound=Callable[..., ResponseReturnValue])


def admin_required(view: FuncType) -> FuncType:  # noqa: UP047
    """Decorator enforcing that the current user is an administrator."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user: CurrentUser | None = load_user()
        if not user:
            return redirect(url_for("auth.login"))
        if not user.is_active_admin:
            logger.warning("User %s tried to access admin-only route", user.username)
            abort(403)
        return view(*args, **kwargs)

    return cast(FuncType, wrapped)


__all__ = [
    "admin_required",
]
