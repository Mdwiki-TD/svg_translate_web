"""
Auth routes — thin HTTP layer for OAuth login, callback, logout.

Responsibilities of this module:
  - Rate limiting at the edge (Flask-Limiter decorators)
  - Reading request data (args, cookies, session keys needed for HTTP)
  - Calling AuthFlowService
  - Translating results into flash messages + redirects

All business logic lives in ``services.auth.flow.AuthFlowService``.
"""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    session,
    url_for,
)
from flask.views import MethodView
from flask_limiter.util import get_remote_address
from werkzeug.wrappers import Response as WerkzeugResponse

from ...config import get_settings
from ...services.auth import AuthFlowService, CurrentUserResolver
from ...services.core.rate_limit import callback_limit, login_limit

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Views (HTTP only)
# ---------------------------------------------------------


class AuthBase(MethodView):
    def __init__(self) -> None:
        self.flow = AuthFlowService()


class LoginView(AuthBase):
    """Start the OAuth flow — redirect user to Meta-Wiki."""

    decorators = [login_limit]

    def get(self) -> WerkzeugResponse:
        logger.info("OAuth login initiated, client: %s", get_remote_address())

        result = self.flow.start_login()

        if not result.success:
            flash(result.error_message or "Login failed", result.flash_category)
            return redirect(
                url_for(
                    "main.index",
                    error=result.error_message or "Login failed",
                )
            )

        return redirect(result.redirect_url)  # type: ignore[arg-type]


class OAuthCallbackView(AuthBase):
    """Handle the OAuth callback from Meta-Wiki."""

    decorators = [callback_limit]

    def get(self) -> WerkzeugResponse:
        logger.info("OAuth callback initiated, client: %s", get_remote_address())

        post_login = session.pop("post_login_redirect", url_for("main.index"))

        result = self.flow.complete_callback(
            request_args=request.args.to_dict(),
            post_login_redirect=post_login,
        )

        if not result.success:
            if result.error_message:
                flash(result.error_message, result.flash_category)
                return redirect(url_for("main.index", error=result.error_message))
            return redirect(url_for("main.index"))

        return result.response  # type: ignore[return-value]


class LogoutView(AuthBase):
    """Log out and delete stored token."""

    def post(self) -> WerkzeugResponse:
        return self._do_logout()

    def get(self) -> WerkzeugResponse:
        return self._do_logout()

    def _do_logout(self) -> WerkzeugResponse:
        app_settings = get_settings()
        cookie_value = request.cookies.get(app_settings.cookie.name)
        session_uid = session.get("uid")

        try:
            uid = int(session_uid) if session_uid is not None else None
        except (TypeError, ValueError):
            uid = None

        result = self.flow.logout(
            session_uid=uid,
            cookie_value=cookie_value,
            index_url=url_for("main.index"),
        )
        flash(result.message, result.flash_category)
        return result.response


class AuthView:
    @classmethod
    def register(cls, bp: Blueprint) -> None:
        # Automatically load the user before any route is processed.
        bp.before_app_request(CurrentUserResolver().set_logged_in_user)
        bp.add_url_rule("/login", view_func=LoginView.as_view("login"))
        bp.add_url_rule("/callback", view_func=OAuthCallbackView.as_view("callback"))
        bp.add_url_rule("/logout", view_func=LogoutView.as_view("logout"))


__all__ = [
    "AuthView",
]
