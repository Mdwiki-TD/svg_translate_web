"""
Authentication helpers and OAuth routes for the web app.
"""

from __future__ import annotations

import logging
import secrets
from collections.abc import Sequence
from typing import Any, cast
from urllib.parse import urlencode

from flask import (
    Blueprint,
    flash,
    g,
    make_response,
    redirect,
    request,
    session,
    url_for,
)
from mwoauth import RequestToken
from werkzeug.wrappers import Response as WerkzeugResponse

from ...config import settings
from ...db.services import delete_user_token
from ...shared.auth.auth_service import (
    OAuthCallbackError,
    complete_oauth_callback,
)
from ...shared.auth.mwoauth_handshake import (
    OAuthIdentityError,
    start_login,
)
from ...shared.core.cookies import (
    extract_user_id,
    sign_state_token,
    sign_user_id,
    verify_state_token,
)
from .rate_limit import callback_rate_limiter, login_rate_limiter
from .utils import load_logged_in_user

logger = logging.getLogger(__name__)

oauth_state_nonce = settings.sessions.state_key
request_token_key = settings.sessions.request_token_key


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def _set_response_cookies(user_id, response) -> None:
    response.set_cookie(
        settings.cookie.name,
        sign_user_id(user_id),
        httponly=settings.cookie.httponly,
        secure=settings.cookie.secure,
        samesite=settings.cookie.samesite,
        max_age=settings.cookie.max_age,
        path="/",
    )


def _client_key() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "anonymous"


def _load_request_token(raw: Sequence[Any] | None) -> RequestToken:
    if not raw:
        raise ValueError("Missing OAuth request token")

    if len(raw) < 2:
        raise ValueError("Invalid OAuth request token")

    return RequestToken(raw[0], raw[1])


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------


class AuthRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.before_app_request
        def before_request() -> None:
            """Automatically load the user before any route is processed."""
            load_logged_in_user()

        @self.bp.get("/login")
        def login() -> WerkzeugResponse:
            logger.info("OAuth login initiated, client: %s", _client_key())
            if not login_rate_limiter.allow(_client_key()):
                time_left = login_rate_limiter.try_after(_client_key()).total_seconds()
                time_left_str = str(time_left).split(".")[0]
                flash(f"Too many login attempts. Please try again after {time_left_str}s.", "warning")
                logger.warning("OAuth login rate limited, client: %s, try_after: %ss", _client_key(), time_left_str)
                return redirect(
                    url_for("main.index", error=f"Too many login attempts. Please try again after {time_left_str}s.")
                )

            state_nonce = secrets.token_urlsafe(32)
            session[oauth_state_nonce] = state_nonce

            # ------------------
            # start login
            try:
                redirect_url, request_token = start_login(sign_state_token(state_nonce))
                logger.info("OAuth login started successfully, redirecting to MediaWiki")
            except (RuntimeError, Exception):
                logger.exception("Failed to start OAuth login")
                flash("Failed to initiate OAuth login", "danger")
                return redirect(url_for("main.index", error="Failed to initiate OAuth login"))

            # ------------------
            # add request_token to session
            session[request_token_key] = cast(list[str], list(request_token))
            logger.debug("OAuth request token stored in session")
            return redirect(redirect_url)

        @self.bp.get("/callback")
        def callback() -> WerkzeugResponse:
            logger.info("OAuth callback initiated, client: %s", _client_key())
            # ------------------
            # callback rate limiter
            if not callback_rate_limiter.allow(_client_key()):
                flash("Too many login attempts", "warning")
                logger.warning("OAuth callback rate limit exceeded, client: %s", _client_key())
                return redirect(url_for("main.index", error="Too many login attempts"))

            # ------------------
            # verify state token
            expected_state = session.pop(oauth_state_nonce, None)
            returned_state = request.args.get("state")
            if not expected_state or not returned_state:
                flash("Invalid OAuth state", "danger")
                logger.warning("OAuth callback failed: missing state token")
                return redirect(url_for("main.index", error="Invalid OAuth state"))

            verified_state = verify_state_token(returned_state)
            if verified_state != expected_state:
                flash("OAuth state mismatch", "danger")
                logger.warning("OAuth callback failed: state mismatch")
                return redirect(url_for("main.index", error="oauth-state-mismatch"))

            # ------------------
            # token data
            raw_request_token = session.pop(request_token_key, None)
            oauth_verifier = request.args.get("oauth_verifier")
            if not raw_request_token or not oauth_verifier:
                flash("Invalid OAuth verifier", "danger")
                logger.warning("OAuth callback failed: missing request token or verifier")
                return redirect(url_for("main.index", error="Invalid OAuth verifier"))

            # ------------------
            # RequestToken
            try:
                request_token = _load_request_token(raw_request_token)
            except ValueError:
                logger.exception("Invalid OAuth request token")
                flash("Invalid OAuth request token", "danger")
                return redirect(url_for("main.index", error="Invalid request token"))

            # ------------------
            # access_token, identity
            try:
                query_string = urlencode(request.args)
                user_record = complete_oauth_callback(request_token, query_string)
            except OAuthIdentityError:
                logger.exception("OAuth identity verification failed")
                flash("Failed to verify OAuth identity", "danger")
                return redirect(url_for("main.index"))
            except OAuthCallbackError as exc:
                logger.exception("OAuth callback failed: %s", exc)
                flash(str(exc), exc.flash_category)
                return redirect(url_for("main.index"))

            user_id = user_record.user_id

            # Set sessions
            session["uid"] = user_id
            session["username"] = user_record.username

            # Set response and cookies
            response = make_response(redirect(session.pop("post_login_redirect", url_for("main.index"))))

            _set_response_cookies(user_id, response)

            # Cache in g for the remainder of THIS request only
            g._current_user = user_record

            return response

        @self.bp.get("/logout")
        def logout() -> WerkzeugResponse:
            user_id = session.pop("uid", None)
            session.pop(request_token_key, None)
            session.pop(oauth_state_nonce, None)
            session.pop("username", None)

            logger.info("Logout requested, user_id: %s", user_id)

            # extract user_id from signed cookie if needed
            if user_id is None:
                signed = request.cookies.get(settings.cookie.name)
                if signed:
                    user_id = extract_user_id(signed)
                    logger.debug("Extracted user_id from cookie: %s", user_id)

            # delete user token if possible
            if isinstance(user_id, int):
                try:
                    delete_user_token(user_id)
                    flash("You have been logged out successfully.", "info")
                    logger.info("User token deleted for user_id: %s", user_id)
                except Exception:
                    logger.exception("Failed to delete user token during logout")
                    flash("Error while clearing OAuth credentials.", "danger")
            else:
                flash("Session cleared.", "info")

            response = make_response(redirect(url_for("main.index")))
            response.delete_cookie(settings.cookie.name, path="/")

            g._current_user = None
            return response


__all__ = [
    "AuthRoutes",
]
