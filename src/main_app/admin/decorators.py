"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar, cast

from flask import (
    abort,
    redirect,
    url_for,
)
from flask.typing import ResponseReturnValue

from ..public.auth.utils import load_user

FuncType = TypeVar("FuncType", bound=Callable[..., ResponseReturnValue])


def admin_required(view: FuncType) -> FuncType:  # noqa: UP047
    """Decorator enforcing that the current user is an administrator."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = load_user()
        if not user:
            return redirect(url_for("auth.login"))
        if not user.is_active_admin:
            abort(403)
        return view(*args, **kwargs)

    return cast(FuncType, wrapped)


__all__ = [
    "admin_required",
]
