"""
Auth routes — thin HTTP layer for OAuth login, callback, logout.

Responsibilities of this module:
  - Rate limiting at the edge
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
from werkzeug.wrappers import Response as WerkzeugResponse

from ...config import get_settings
from ...services.auth.current_user_resolver import CurrentUserResolver
from ...services.auth.flow import AuthFlowService
from ...services.core.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Views (HTTP only)
# ---------------------------------------------------------


class AuthBase(MethodView):
    def __init__(self) -> None:
        self.flow = AuthFlowService()


class LoginView(AuthBase):
    """Start the OAuth flow — redirect user to Meta-Wiki."""

    def get(self) -> WerkzeugResponse:
        # -----
        # check rate limit
        # -----
        key = RateLimiter.client_key(request)

        logger.info("OAuth login initiated, client: %s", key)
        login_rate_limiter = RateLimiter.login_rate_limiter()

        if not login_rate_limiter.allow(key):
            time_left = login_rate_limiter.get_time_left(key)
            msg = f"Too many login attempts. Please try again after {time_left}s."
            flash(msg, "warning")
            logger.warning(
                "OAuth login rate limited, client: %s, try_after: %ss",
                key,
                time_left,
            )
            return redirect(url_for("main.index", error=msg))

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

    def get(self) -> WerkzeugResponse:
        key = RateLimiter.client_key(request)

        logger.info("OAuth callback initiated, client: %s", key)
        # ------------------
        # callback rate limiter
        callback_rate_limiter = RateLimiter.callback_rate_limiter()

        if not callback_rate_limiter.allow(key):
            flash("Too many login attempts", "warning")
            logger.warning("OAuth callback rate limit exceeded, client: %s", key)
            return redirect(url_for("main.index", error="Too many login attempts"))

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
