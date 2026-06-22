"""
Authentication helpers and OAuth routes for the web app.
"""

from __future__ import annotations

import logging
import secrets
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlencode

from flask import (
    Blueprint,
    Response,
    flash,
    g,
    make_response,
    redirect,
    request,
    session,
    url_for,
)
from mwoauth import RequestToken

from ...config import settings
from ...core.cookies import extract_user_id, sign_state_token, sign_user_id, verify_state_token
from ...db.services import delete_user_token
from ...su_services.auth_service import OAuthCallbackError, complete_oauth_callback
from ...su_services.mwoauth_handshake import OAuthIdentityError, start_login
from .rate_limit import callback_rate_limiter, login_rate_limiter
from .utils import load_logged_in_user

logger = logging.getLogger(__name__)
bp_auth = Blueprint("auth", __name__)

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
# Hooks
# ---------------------------------------------------------


# Register the hook right after defining the blueprint
@bp_auth.before_app_request
def before_request() -> None:
    """Automatically load the user before any route is processed."""
    load_logged_in_user()


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------


@bp_auth.get("/login")
def login() -> Response:
    if not login_rate_limiter.allow(_client_key()):
        time_left = login_rate_limiter.try_after(_client_key()).total_seconds()
        time_left = str(time_left).split(".")[0]
        flash(f"Too many login attempts. Please try again after {time_left}s.", "warning")
        return redirect(url_for("main.index"))

    state_nonce = secrets.token_urlsafe(32)
    session[oauth_state_nonce] = state_nonce

    # ------------------
    # start login
    try:
        redirect_url, request_token = start_login(sign_state_token(state_nonce))
    except Exception:
        logger.exception("Failed to start OAuth login")
        flash("Failed to initiate OAuth login", "danger")
        return redirect(url_for("main.index"))

    # ------------------
    # add request_token to session
    session[request_token_key] = list(request_token)
    return redirect(redirect_url)


@bp_auth.get("/callback")
def callback() -> Response:
    # ------------------
    # callback rate limiter
    if not callback_rate_limiter.allow(_client_key()):
        flash("Too many login attempts", "warning")
        return redirect(url_for("main.index"))

    # ------------------
    # verify state token
    expected_state = session.pop(oauth_state_nonce, None)
    returned_state = request.args.get("state")
    if not expected_state or not returned_state:
        flash("Invalid OAuth state", "danger")
        return redirect(url_for("main.index"))

    verified_state = verify_state_token(returned_state)
    if verified_state != expected_state:
        flash("OAuth state mismatch", "danger")
        return redirect(url_for("main.index"))

    # ------------------
    # token data
    raw_request_token = session.pop(request_token_key, None)
    oauth_verifier = request.args.get("oauth_verifier")
    if not raw_request_token or not oauth_verifier:
        flash("Invalid OAuth verifier", "danger")
        return redirect(url_for("main.index"))

    # ------------------
    # RequestToken
    try:
        request_token = _load_request_token(raw_request_token)
    except ValueError:
        logger.exception("Invalid OAuth request token")
        flash("Invalid OAuth request token", "danger")
        return redirect(url_for("main.index"))

    # ------------------
    # access_token, identity
    try:
        user_record = complete_oauth_callback(request_token, urlencode(request.args))
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


@bp_auth.get("/logout")
def logout() -> Response:
    """
    TODO: Users with stale cookies will be redirected with a "login-required" error
    instead of being able to clean up their authentication state
    """
    user_id = session.pop("uid", None)
    session.pop(request_token_key, None)
    session.pop(oauth_state_nonce, None)
    session.pop("username", None)

    # extract user_id from signed cookie if needed
    if user_id is None:
        signed = request.cookies.get(settings.cookie.name)
        if signed:
            user_id = extract_user_id(signed)

    # delete user token if possible
    if isinstance(user_id, int):
        try:
            delete_user_token(user_id)
            flash("You have been logged out successfully.", "info")
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
    "bp_auth",
]
