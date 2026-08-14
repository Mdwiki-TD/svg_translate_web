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

from ...config import settings
from ...services.auth.flow import AuthFlowService
from ...services.auth.utils import set_logged_in_user
from .rate_limit import callback_rate_limiter, login_rate_limiter

logger = logging.getLogger(__name__)


def _client_key() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "anonymous"


# ---------------------------------------------------------
# Views (HTTP only)
# ---------------------------------------------------------


class LoginView(MethodView):
    """Start the OAuth flow — redirect user to Meta-Wiki."""

    def get(self) -> WerkzeugResponse:
        # -----
        # check rate limit
        # -----
        key = _client_key()
        logger.info("OAuth login initiated, client: %s", key)

        if not login_rate_limiter.allow(key):
            time_left = login_rate_limiter.get_login_rate_limit_seconds(key)
            msg = f"Too many login attempts. Please try again after {time_left}s."
            flash(msg, "warning")
            logger.warning(
                "OAuth login rate limited, client: %s, try_after: %ss",
                key,
                time_left,
            )
            return redirect(url_for("main.index", error=msg))

        flow = AuthFlowService()

        result = flow.start_login()

        if not result.success:
            flash(result.error_message or "Login failed", result.flash_category)
            return redirect(
                url_for(
                    "main.index",
                    error=result.error_message or "Login failed",
                )
            )

        return redirect(result.redirect_url)  # type: ignore[arg-type]


class OAuthCallbackView(MethodView):
    """Handle the OAuth callback from Meta-Wiki."""

    def get(self) -> WerkzeugResponse:
        key = _client_key()
        logger.info("OAuth callback initiated, client: %s", key)
        # ------------------
        # callback rate limiter
        if not callback_rate_limiter.allow(key):
            flash("Too many login attempts", "warning")
            logger.warning("OAuth callback rate limit exceeded, client: %s", key)
            return redirect(url_for("main.index", error="Too many login attempts"))

        flow = AuthFlowService()
        post_login = session.pop("post_login_redirect", url_for("main.index"))

        result = flow.complete_callback(
            request_args=request.args.to_dict(),
            post_login_redirect=post_login,
        )

        if not result.success:
            if result.error_message:
                flash(result.error_message, result.flash_category)
                return redirect(url_for("main.index", error=result.error_message))
            return redirect(url_for("main.index"))

        return result.response  # type: ignore[return-value]


class LogoutView(MethodView):
    """Log out and delete stored token."""

    def post(self) -> WerkzeugResponse:
        return self._do_logout()

    def get(self) -> WerkzeugResponse:
        return self._do_logout()

    def _do_logout(self) -> WerkzeugResponse:
        flow = AuthFlowService()
        cookie_value = request.cookies.get(settings.cookie.name)
        session_uid = session.get("uid")

        try:
            uid = int(session_uid) if session_uid is not None else None
        except (TypeError, ValueError):
            uid = None

        result = flow.logout(
            session_uid=uid,
            cookie_value=cookie_value,
            index_url=url_for("main.index"),
        )
        flash(result.message, result.flash_category)
        return result.response


class AuthRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        # Automatically load the user before any route is processed.
        self.bp.before_app_request(set_logged_in_user)

        self.bp.add_url_rule("/login", view_func=LoginView.as_view("login"))
        self.bp.add_url_rule("/callback", view_func=OAuthCallbackView.as_view("callback"))
        self.bp.add_url_rule("/logout", view_func=LogoutView.as_view("logout"))


__all__ = [
    "AuthRoutes",
]
