"""
Auth routes — OAuth login, callback, logout.
"""

from __future__ import annotations

import logging
import secrets
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
from flask.views import MethodView
from mwoauth import AccessToken
from werkzeug.wrappers import Response as WerkzeugResponse

from ...config import settings
from ...database.services import UsersService
from ...services.auth.auth_exceptions import (
    OAuthCallbackError,
    OAuthIdentityError,
)
from ...services.auth.auth_service import OAuthService
from ...services.auth.token_manager import TokenManager
from ...services.auth.utils import set_logged_in_user
from ...services.core.cookies import (
    extract_user_id,
    sign_state_token,
    sign_user_id,
    verify_state_token,
)
from .rate_limit import callback_rate_limiter, login_rate_limiter

logger = logging.getLogger(__name__)

request_secret_key = settings.sessions.request_secret_key
request_token_key = settings.sessions.request_token_key
oauth_state_nonce = settings.sessions.state_key

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def _client_key() -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "anonymous"


class AuthHelper:
    """Builds OAuth and TokenManager instances."""

    def __init__(self) -> None:
        self.oauth_service: OAuthService = OAuthService(
            consumer_key=settings.oauth.consumer_key,
            consumer_secret=settings.oauth.consumer_secret,
            oauth_mwuri=settings.oauth.mw_uri,
            user_agent=settings.other.user_agent,
        )
        self.token_manager: TokenManager = TokenManager()

        self.rate_limiter_key = _client_key()
        self.user_svc = UsersService()

    def _resolve_user_id(self, username: str) -> int:
        """Return the user_id for ``username``, creating a UserRecord if needed."""
        record = self.user_svc.ensure_exists(username)
        return record.user_id


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------


class LoginView(AuthHelper, MethodView):
    """Start the OAuth flow — redirect user to Meta-Wiki."""

    def get(self):
        return self.login()

    def login(self) -> WerkzeugResponse:
        # -----
        # check rate limit
        # -----
        _key = self.rate_limiter_key
        logger.info("OAuth login initiated, client: %s", _key)
        if not login_rate_limiter.allow(_key):
            time_left_str = login_rate_limiter.get_login_rate_limit_seconds(_key)
            flash(f"Too many login attempts. Please try again after {time_left_str}s.", "warning")
            logger.warning("OAuth login rate limited, client: %s, try_after: %ss", _key, time_left_str)
            return redirect(
                url_for("main.index", error=f"Too many login attempts. Please try again after {time_left_str}s.")
            )

        # ------------------
        # start login
        state_nonce = secrets.token_urlsafe(32)
        session[oauth_state_nonce] = state_nonce

        callback_url = url_for(
            "auth.callback",
            _external=True,
            state=sign_state_token(state_nonce),
        )
        try:
            auth_url, request_token, request_secret = self.oauth_service.create_authorization_url(callback_url)
            logger.info("OAuth login started successfully, redirecting to MediaWiki")
        except (RuntimeError, Exception):
            logger.exception("Failed to start OAuth login")
            flash("Failed to initiate OAuth login", "danger")
            return redirect(url_for("main.index", error="Failed to initiate OAuth login"))

        # ------------------
        # Store request token in session for the callback step
        session[request_token_key] = request_token
        session[request_secret_key] = request_secret

        logger.debug("OAuth request token stored in session")
        return redirect(auth_url)


class OAuthCallbackView(AuthHelper, MethodView):
    """Handle the OAuth callback from Meta-Wiki."""

    def get(self):
        return self.callback()

    def callback(self) -> WerkzeugResponse:
        _key = self.rate_limiter_key
        logger.info("OAuth callback initiated, client: %s", _key)
        # ------------------
        # callback rate limiter
        if not callback_rate_limiter.allow(_key):
            flash("Too many login attempts", "warning")
            logger.warning("OAuth callback rate limit exceeded, client: %s", _key)
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
        oauth_verifier = request.args.get("oauth_verifier")

        request_token = session.pop(request_token_key, None)
        request_secret = session.pop(request_secret_key, None)

        if not request_token or not request_secret or not oauth_verifier:
            flash("Invalid OAuth verifier", "danger")
            logger.warning("OAuth callback failed: missing request token or verifier")
            return redirect(url_for("main.index"))

        # ------------------
        # RequestToken
        query_string = urlencode(request.args)

        try:
            token_data: AccessToken = self.oauth_service.fetch_access_token(
                query_string=query_string,
                oauth_token=request_token,
                oauth_token_secret=request_secret,
            )
        except OAuthCallbackError as exc:
            logger.exception("OAuth callback failed: %s", exc)
            flash(str(exc), exc.flash_category)
            return redirect(url_for("main.index"))
        except Exception as exc:
            logger.exception("OAuth callback failed: %s", exc)
            return redirect(url_for("main.index"))

        # ------------------
        # access_token, identity
        # Identify the user

        try:
            identity = self.oauth_service.identify(token_data)
        except OAuthIdentityError:
            logger.exception("OAuth identity verification failed")
            flash("Failed to verify OAuth identity", "danger")
            return redirect(url_for("main.index"))

        except OAuthCallbackError as exc:
            logger.exception("OAuth callback failed: %s", exc)
            flash(str(exc), exc.flash_category)
            return redirect(url_for("main.index"))

        username = identity.get("username") or identity.get("name") or ""

        if not username:
            logger.error("OAuth callback failed: missing username in identity")
            flash("Missing username in OAuth identity", "danger")
            return redirect(url_for("main.index"))

        # Persist the user record (and obtain its stable user_id) before
        # saving the encrypted token, which is keyed by user_id.
        try:
            user_id = self._resolve_user_id(username)
        except Exception as exc:
            logger.exception("Failed to resolve user ID: %s", exc)
            flash("Failed to resolve user ID", "danger")
            return redirect(url_for("main.index"))

        # Save encrypted token
        user_record = self.token_manager.save_token(
            user_id=user_id,
            access_token=token_data.key,
            access_secret=token_data.secret,
        )
        if not user_record:
            logger.error("OAuth callback failed while saving user credentials")
            flash("Failed to process user credentials", "danger")
            return redirect(url_for("main.index"))

        # Set sessions
        session["uid"] = user_id
        session["username"] = username

        # Set response and cookies
        response = make_response(redirect(session.pop("post_login_redirect", url_for("main.index"))))

        self._set_response_cookies(user_id, response)

        # Cache in g for the remainder of THIS request only
        g._current_user = user_record

        return response

    @staticmethod
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


class LogoutView(AuthHelper, MethodView):
    """Log out and delete stored token."""

    def post(self):
        return self.logout()

    def get(self):
        return self.logout()

    def logout(self) -> WerkzeugResponse:
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
                self.token_manager.delete_token(user_id)
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


class AuthRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        # super.__init__()
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.before_app_request(self.before_request)
        self.bp.add_url_rule("/login", view_func=LoginView.as_view("login"))
        self.bp.add_url_rule("/callback", view_func=OAuthCallbackView.as_view("callback"))
        self.bp.add_url_rule("/logout", view_func=LogoutView.as_view("logout"))

    def before_request(self) -> None:
        """Automatically load the user before any route is processed."""
        set_logged_in_user()


__all__ = [
    "AuthRoutes",
]
