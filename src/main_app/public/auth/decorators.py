"""
Authentication utilities and decorators for routes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flask import redirect, render_template, request, session, url_for

from ...api_services.clients import get_user_groups
from ...services.auth.utils import get_current_user

FuncType = TypeVar("FuncType", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


AUTOPATROL_GROUPS = frozenset({"autopatrol", "autopatrolled"})
AUTOPATROL_REQUEST_URL = "https://commons.wikimedia.org/wiki/Commons:Requests_for_rights#Autopatrol"


def oauth_required(func: FuncType) -> FuncType:  # noqa: UP047
    """Decorator that requires a full OAuth credential bundle."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check g._current_user which was populated by set_logged_in_user
        user = get_current_user()
        if not user:
            session["post_login_redirect"] = request.url
            return redirect(url_for("auth.login"))

        return func(*args, **kwargs)

    return cast(FuncType, wrapper)


def autopatrol_required(func: FuncType) -> FuncType:  # noqa: UP047
    """Require an authenticated Commons user to hold Autopatrol permission."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user = get_current_user()
        if not user:
            session["post_login_redirect"] = request.url
            return redirect(url_for("auth.login"))

        groups = get_user_groups(user.to_auth_payload())
        if groups is None:
            return render_template("permission_check_unavailable.html"), 503

        if not groups.intersection(AUTOPATROL_GROUPS):
            return (
                render_template(
                    "autopatrol_required.html",
                    autopatrol_request_url=AUTOPATROL_REQUEST_URL,
                ),
                403,
            )

        return func(*args, **kwargs)

    return cast(FuncType, wrapper)


__all__ = [
    "AUTOPATROL_GROUPS",
    "AUTOPATROL_REQUEST_URL",
    "autopatrol_required",
    "oauth_required",
]
